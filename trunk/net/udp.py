#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

import time
import thread
import threading
import socket
import sys
import traceback
import re

class Packet(object):
	# Timeout before packet is resend
	timeout = 0.005

	# Timeout before packet is said to be "lost"
	total_timeout = 3.000 

	# Maximum number of packet resend
	max_resend = int(3.000 / timeout)
	
	# Constructor
	# data (optionnal) is a binary packet
	def __init__(self, data=None):
		self.sent = 0
		self.__data = None
		self.timeout = None
		self.skippable = False
		self.id = None
		self.unpack(data)

	# After unpack, say if the packet is valid or not
	def isValid(self):
		return self.__data != None
		
	# For debug only, convert to string
	def toStr(self):
		return "\"%s\" [id=%u, skippable=%u]" \
			% (self.__data, self.id, self.skippable)

	# Fill attributs from a binary data packet
	def unpack(self, data):
		if data==None: return
		m = re.compile("^([0-9]+):([0-9]+):(.+)$").match(data)
		if m == None: return
		self.skippable = (m.group(1) == '1')
		self.id = int(m.group(2))
		self.__data = m.group(3)

	# Pack datas to a binary string (using struct module)
	def pack(self):
		return "%u:%u:%s" \
			% (self.skippable, self.id, self.__data)
		
	# Write a sting into packet
	def writeStr(self, str):
		if self.__data == None:
			self.__data = str
		else:
			self.__data = self.__data + str
		
	# Prepare the packet before it will be send
	def prepareSend(self):
		self.timeout = time.time()+Packet.timeout
		self.sent = self.sent + 1

	#-- Properties --------------------------------------------------------------
	def getData(self): return self.__data
	data = property(getData)	

class IO_UDP:
	def __init__(self, is_server=False):
		self.debug = False
		self.packet_timeout = 1.000
		self.thread_receive = True
		self.thread_sleep = 0.010

		self.__is_server = is_server

		self.__socket = None
		self.__addr = None
		self.__packet_id = 0
		self.__clients = []
		self.__waitAck = {}
		self.__received = {}
		self.__waitAck_sema = threading.Semaphore()
		self.__received_sema = threading.Semaphore()

	# Connect to a server if __is_server=True
	# Bind a port else
	def connect(self, host, port):
		self.__addr = (host, port,)
		self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		if self.__is_server:
			print "Run server at %s:%u" % (self.__addr[0], self.__addr[1])
			self.__socket.bind(self.__addr)
		else:
			print "Connect to server %s:%u" % (self.__addr[0], self.__addr[1])			
		self.__socket.setblocking(0)
	
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

	# Action when a new client is detected
	def connectClient(self, addr):
		self.__clients.append(addr)
		print "New client : %s:%u" % (addr[0], addr[1])

	# Read a packet from the socket
	# Returns None if there is not new data
	def receive(self, max_size = 1024):
		# Try to read data from the socket
		try:						
			data,addr = self.__socket.recvfrom(max_size)
		except socket.error, err:
			if err[0] == 11: return None
			raise

		if self.debug: print "Received packet (\"%s\" from %s:%u)" % (data, addr[0], addr[1])
		
		# New client ?
		if self.__is_server:
			if addr not in self.__clients:
				self.connectClient(addr)

		# Is it an ack ?
		m = re.compile("^ACK ([0-9]+)$").match(data)
		if m != None:
			self.__processAck(int(m.group(1)))
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
			while 1:
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

	#--- Private functions ------------------------------------------------------
	
	# Send an ack for a packet
	def __sendAck(self, packet, addr):
		# Write ack to socket
		data = "ACK %u" % (packet.id)
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

def loop_server(io):
	io.thread_sleep = 0.010
	thread.start_new_thread( io.run_thread, ())
	while 1:
		msg = raw_input(">> ")
		if msg=="": break
		packet = Packet()
		packet.writeStr(msg)
		io.send(packet)
		time.sleep(0.100)
		print ""
		
def loop_client(io):
	io.thread_receive = False
	thread.start_new_thread( io.run_thread, ())
	
	while 1:
		msg = raw_input(">> ")
		if msg=="": break
		
		m = re.compile("^eval:(.+)$").match(msg)
		if m != None: msg = eval(m.group(1))			
		
		packet = Packet()
		packet.writeStr(msg)
		if msg[0]=='0':			
			packet.skippable = True
		io.send(packet)
		io.thread_receive = True
		time.sleep(0.100)
		print ""

def main():
	is_server = False
	for arg in sys.argv[1:]:
		if arg=="--server": is_server = True
	io = IO_UDP(is_server)
	io.debug = True
	port = 12430
	if is_server:
		host = ''
	else:
		host = 'localhost'
#		host = 'tchoy.net'
#		host = '10.20.0.117'
	io.connect(host, port)	

	try:
		if is_server:
			loop_server(io)
		else:
			loop_client(io)
	except KeyboardInterrupt:
		print "\nProgramme interrompu (CTRL+C)."
	
if __name__=="__main__": main()
