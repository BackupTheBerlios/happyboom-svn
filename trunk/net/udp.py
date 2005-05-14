#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

import time
import threading
import socket
import traceback
import struct
from packet import Packet
from udp_client import UDP_Client
from base_io import BaseIO

class IO_UDP(BaseIO):
	def __init__(self, is_server=False):
		BaseIO.__init__(self)
		self.packet_timeout = 1.000
		self.thread_sleep = 0.010

		self.__is_server = is_server
		self.__server = None # only used in client mode
		self.loop = True

		self.__socket = None
		self.__socket_open = False		
		self.__addr = None
		self.__packet_id = 0
		self.__clients = {}
		self.__clients_sema = threading.Semaphore()

	# Connect to host:port
	def connect(self, host, port):
		host = socket.gethostbyname(host)
		self.__addr = (host, port,)
		self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		if self.__is_server:
			if self.verbose:
				print "Run server at %s:%u" % (self.host, self.port)
			self.__socket.bind(self.__addr)
		else:
			if self.verbose:
				print "Connect to server %s:%u" % (self.host, self.port)
			self.__server = UDP_Client(self, self.__addr)
#			self.__server.send_ping = True
			self.__clients_sema.acquire()
			self.__clients[self.__addr] = self.__server
			self.__clients_sema.release()

		self.__socket_open = True
		self.__socket.setblocking(0)

		if not self.__is_server:
			self.send( Packet("I'm here") )
		
		if self.on_connect != None: self.on_connect()

	# Close connection
	def disconnect(self):
		if not self.__socket_open: return
		self.__socket.close()
		self.__socket_open = False
		if self.on_disconnect != None: self.on_disconnect()

	# Disconnect a client.
	def disconnectClient(self, client):
		self.__clients_sema.acquire()
		del self.__clients[client.addr]
		self.__clients_sema.release()
		if self.verbose:
			print "Disconnect client %s" % (client.name)
		if self.on_client_disconnect != None: self.on_client_disconnect(client)
	
	# Send a packet to the server or to all clients
	def send(self, packet, to=None):
		if not self.__socket_open: return
		first_send = (packet.sent == 0)
		
		# No client, exit !
		if self.__is_server:
			self.__clients_sema.acquire()
			nb_clients = len(self.__clients)
			self.__clients_sema.release()
			if nb_clients==0: return None

		# Prepare the packet
		packet.prepareSend()
		if first_send:
			# First send : give an ID to the packet
			self.__packet_id = self.__packet_id + 1
			packet.id = self.__packet_id
			if self.debug: packet.creation = time.time()
		need_ack = first_send and not packet.skippable
		
		# Read binary version of the packet
		data = packet.pack()
		if self.debug:
			t = time.time() - packet.creation
			print "Send data : \"%s\" (time=%.1f ms)." % (data, 1000*t)

		if self.__is_server:
			if to==None:
				for addr,client in self.clients.items(): # use internal copy for clients
					self.__sendDataTo(packet, data, client, need_ack)
			else:
				self.__sendDataTo(packet, data, to, need_ack)
		else:
			self.__sendDataTo(packet, data, self.__server, need_ack)
			
	def __sendDataTo(self, packet, data, client, need_ack):
		addr = client.addr

		if self.debug:
			print "Send [id=%u] %s to %s:%u" \
				% (packet.id, packet.data, addr[0], addr[1])
		self.__socket.sendto(data, addr)

		# If the packet need an ack, add it to the list
		if need_ack: client.needAck(packet)
	
	# Read a packet from the socket
	# Returns None if there is not new data
	def receive(self, max_size = 1024):
		if not self.__socket_open: return None

		# Try to read data from the socket
		try:						
			data,addr = self.__socket.recvfrom(max_size)
		except socket.error, err:
			if err[0] == 11: return None
			raise

		if self.debug:
			print "Received packet (\"%s\" from %s:%u)" % (data, addr[0], addr[1])
		
		# New client ?
		return self.__processRecvData(data, addr)

	# Keep the connection alive
	def live(self):				
		# Resend packets which don't have received their ack
		for addr, client in self.clients.items(): # use internal copy for clients
			client.live()							
					
		# Read data from network (if needed)
		packet = self.receive()				
		if packet != None: self.__processNewPacket(packet)
					

	def clientLostConnection(self, client):
		if self.__is_server:
			self.__lostClient(client)
		else:
			self.lostConnection()

	def __lostClient(self, client):
		client = self.__clients[client.addr]
		if self.verbose:
			print "Lost connection with client %s !" % (client.name)
		self.disconnectClient(client)
	
	def lostConnection(self):
		if self.verbose:
			print "Lost connection to %s:%u!" % (self.host, self.port)
		self.loop = False
		if self.__socket_open:
			self.__socket.close()
			self.__socket_open = False
		if self.on_lost_connection: self.on_lost_connection()
	
	# Function which should be called in a thread
	def run_thread(self):
		try:
			while self.loop:
				self.live()				
				time.sleep(self.thread_sleep)
		except Exception, msg:
			print "EXCEPTION DANS LE THREAD IO :"
			print msg
			traceback.print_exc()

	def stop(self):
		self.loop = False
		self.disconnect()

	#--- Private functions ------------------------------------------------------

	def __processRecvData(self, data, addr):
		if self.__is_server:
			self.__clients_sema.acquire()
			if addr not in self.__clients:
				client = UDP_Client(self, addr)
				self.__clients[addr] = client
				self.__clients_sema.release()
				if self.verbose: print "New client : %s:%u" % (addr[0], addr[1])
#				client.send_ping = True
				if self.on_client_connect != None: self.on_client_connect(client)
			else:
				client = self.__clients[addr] 
				self.__clients_sema.release()
		else:
			# Drop packets which doesn't come from server
			if self.__server.addr != addr:
				if self.debug:
					print "Drop packet from %s:%u" % (addr[0], addr[1])
				return None
			client = self.__server
	
		# Is it an ack ?
		format = "!cI"
		if len(data) == struct.calcsize(format):
			ack = struct.unpack(format, data)
			client.processAck(ack[1])
			return None

		# Decode data to normal packet (unpack) 
		packet = Packet()
		packet.unpack(data)
		if not packet.isValid(): return None

		packet.recv_from = client 
		return self.__processPacket(packet)

	def __processPacket(self, packet):
		client = packet.recv_from
		addr = client.addr
	
		# Send an ack if needed
		if not packet.skippable: self.__sendAck(packet)
			
		# This packet is already received ? Drop it!
		if client.alreadyReceived(packet.id):
			if self.debug:
				print "Drop packet %u (already received)" % (packet.id)
			return None	
			
		client.receivePacket(packet)
		
		# Returns the new packet
		return packet

	# Send an ack for a packet
	def __sendAck(self, packet):
		# Write ack to socket
		data = struct.pack("!cI", 'A', packet.id)
		if self.debug: print "Send ACK : \"%s\"." % (data)
		self.__socket.sendto(data, packet.recv_from.addr)

	# Do something with a new packet
	def __processNewPacket(self, packet):
		if self.verbose:
			print "New udp message : %s" % (packet.toStr())
		if self.on_new_packet != None: self.on_new_packet(packet)		

	def __getPort(self):
		return self.__addr[1]

	def __getHost(self):
		if self.__addr[0]=='': return "localhost"
		return self.__addr[0]

	def __getAddr(self): return self.__addr

	def __getName(self):
		if self.__name != None: return self.__name
		return self.host
		
	def __setName(self, name):
		self.__name = name	

	def __getClients(self):
		self.__clients_sema.acquire()
		clients = self.__clients.copy()
		self.__clients_sema.release()
		return clients

	def __getMaxClients(self):
		return 0
		
	#--- Properties -------------------------------------------------------------

	name = property(__getName, __setName)
	addr = property(__getAddr)
	port = property(__getPort)
	host = property(__getHost)
	clients = property(__getClients)
	max_clients = property(__getMaxClients)
