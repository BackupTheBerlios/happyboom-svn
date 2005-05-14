#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

import time
import threading
import socket
import traceback
import struct
from packet import Packet

class IO_UDP(object):
	def __init__(self, is_server=False):
		self.debug = False
		self.verbose = True 
		self.packet_timeout = 1.000
		self.thread_receive = True
		self.thread_sleep = 0.010

		# Events
		self.on_connect = None            # No argument
		self.on_lost_connection = None    # No argument
		self.on_disconnect = None         # No argument
		self.on_new_client = None         # (addr) : client address

		self.__is_server = is_server
		self.loop = True

		self.__socket = None
		self.__socket_open = False		
		self.__addr = None
		self.__packet_id = 0
		self.__clients = []
		self.__waitAck = {}
		self.__received = {}
		self.__waitAck_sema = threading.Semaphore()
		self.__received_sema = threading.Semaphore()
		self.__name = None

	# Connect to a server if __is_server=True
	# Bind a port else
	def connect(self, host, port):
		self.__addr = (host, port,)
		self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		if self.__is_server:
			if self.verbose:
				print "Run server at %s:%u" % (self.__addr[0], self.__addr[1])
			self.__socket.bind(self.__addr)
		else:
			if self.verbose:
				print "Connect to server %s:%u" % (self.__addr[0], self.__addr[1])			
		self.__socket_open = True
		self.__socket.setblocking(0)
		if self.on_connect != None: self.on_connect()

	# Close connection
	def disconnect(self):
		if not self.__socket_open: return
		self.__socket.close()
		self.__socket_open = False
		if self.on_disconnect != None: self.on_disconnect()
	
	# Send a packet to the server or to all clients
	def send(self, packet):
		# If we are a server and their is no client : exit!
		if self.__is_server and len(self.__clients)==0: return
		
		# Prepare the packet
		packet.prepareSend()
		if packet.sent == 1:
			# First send : give an ID to the packet
			self.__packet_id = self.__packet_id + 1
			packet.id = self.__packet_id
			if self.debug: packet.creation = time.time()

			# If the packet need an ack, add it to the list
			if not packet.skippable:				
				self.__waitAck[packet.id] = packet
		
		# Read binary version of the packet
		data = packet.pack()
		if self.debug:
			t = time.time() - packet.creation
			print "Send data : \"%s\" (time=%.1f ms)." % (data, 1000*t)

		# Write data to the socket
		if self.__is_server:
			for client in self.__clients:
				self.__socket.sendto(data, client)
		else:
			self.__socket.sendto(data, self.__addr)

	# Read a packet from the socket
	# Returns None if there is not new data
	def receive(self, max_size = 1024):
		# Try to read data from the socket
		try:						
			data,addr = self.__socket.recvfrom(max_size)
		except socket.error, err:
			if err[0] == 11: return None
			raise

		if self.debug:
			print "Received packet (\"%s\" from %s:%u)" % (data, addr[0], addr[1])
		
		# New client ?
		if self.__is_server:
			if addr not in self.__clients:
				self.__connectClient(addr)

		# Is it an ack ?
		format = "!cI"
		if len(data) == struct.calcsize(format):
			ack = struct.unpack(format, data)
			self.__processAck(ack[1])
			return None

		# Decode data to normal packet (unpack) 
		packet = Packet(data)
		if not packet.isValid(): return None
		
		# Send an ack if needed
		if not packet.skippable: self.__sendAck(packet, addr)
			
		# This packet is already received ? Drop it!
		self.__received_sema.acquire()
		drop = packet.id in self.__received
		self.__received_sema.release()
		if drop:
			if self.debug:
				print "Drop packet %u (already received)" % (packet.id)
			return None	
			
		# Store packet to drop packet which are receive twice
		if not packet.skippable:
			self.__received_sema.acquire()
			self.__received[packet.id] = time.time()+Packet.total_timeout
			self.__received_sema.release()
		
		# Returns the new packet
		return packet

	# Keep the connection alive
	def live(self):				
		# Resend packets which don't have received their ack
		self.__waitAck_sema.acquire()
		waitAckCopy = self.__waitAck.copy()
		self.__waitAck_sema.release()
		for id in waitAckCopy:
			packet = self.__waitAck[id]
			if packet.timeout < time.time():
				if packet.sent < Packet.max_resend:
					self.send(packet)
				else:
					raise Exception, "Paquet envoyé plus de %u fois !" % (Packet.max_resend)		
					
		# Clean old received packets 
		self.__received_sema.acquire()
		receivedCopy = self.__received.copy()
		self.__received_sema.release()
		for id in receivedCopy:
			if self.__received[id] < time.time():
				if self.debug: print "Supprime ancien paquet %u (timeout)" % (id)
				del self.__received[id]
	
	# Function which should be called in a thread
	def run_thread(self):
		try:
			while self.loop:
				self.live()				
				if self.thread_receive:
					packet = self.receive()				
					if packet != None:
						print "[chat] New message : %s" % (packet.toStr())
				time.sleep(self.thread_sleep)
		except Exception, msg:
			print "EXCEPTION DANS LE THREAD IO :"
			print msg
			print "--"			
			traceback.print_exc()

	def stop(self):
		self.loop = False
		self.disconnect()

	#--- Private functions ------------------------------------------------------

	# Action when a new client is detected
	def __connectClient(self, addr):
		self.__clients.append(addr)
		if self.verbose: print "New client : %s:%u" % (addr[0], addr[1])
		if self.on_new_client != None: self.on_new_client(addr)
	
	# Send an ack for a packet
	def __sendAck(self, packet, addr):
		# Write ack to socket
		data = struct.pack("!cI", 'A', packet.id)
		if self.debug: print "Send ACK : \"%s\"." % (data)
		self.__socket.sendto(data, addr)

	# Process an ack
	def __processAck(self, id):
		if self.__waitAck.has_key(id):			
			# Debug message
			if self.debug:
				t = time.time() - self.__waitAck[id].creation
				print "Ack %u received (time=%.1f ms)" % (id, t*1000)

			# The packet don't need ack anymore
			del self.__waitAck[id]
		else:
			# Ack already received
			if self.debug: print "No more packet %u" % (id)
	
	def __getPort(self):
		return self.__addr[1]

	def __getHost(self):
		if self.__addr[0]=='': return "localhost"
		return self.__addr[0]

	def __getName(self):
		if self.__name != None: return self.__name
		return self.host
		
	def __setName(self, name):
		self.__name = name	
		
	#--- Properties -------------------------------------------------------------

	name = property(__getName, __setName)
	port = property(__getPort)
	host = property(__getHost)
