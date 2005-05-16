#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

import time
import thread
import threading
import socket
import traceback
import struct
from tcp_client import TCP_Client
from net import io
from server_waiter import NetworkServerWaiter

class IO_TCP(io.BaseIO):
	def __init__(self, is_server=False):
		io.BaseIO.__init__(self)
		self.packet_timeout = 1.000
		self.thread_sleep = 0.010

		self.__is_server = is_server

		self.__waiter = NetworkServerWaiter(self)
		self.__addr = None
		self.__clients = {}
		self.__server = None
		self.__clients_sema = threading.Semaphore()
		self.__running = True
		io.Packet.use_tcp = True

	# Connect to host:port
	def connect(self, host, port):
		max_connection = 50
	
		self.__addr = (host, port,)
		if self.__is_server:
			if self.verbose:
				print "Run server at %s:%u" % (self.host, self.port)
			thread.start_new_thread( self.__waiter.run_thread, (port,max_connection,))
		else:
			if self.verbose:
				print "Connect to server %s:%u" % (self.host, self.port)			
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect(self.__addr)

			client = TCP_Client(self, self.__addr, socket=s)
			self.__server = client
			self.__clients_sema.acquire()
			self.__clients[client.addr] = client
			self.__clients_sema.release()

		if self.on_connect != None: self.on_connect()
		io.BaseIO.connect(self, host, port)

	# Close connection
	def disconnect(self):
		self.__clients_sema.acquire()
		clients = self.__clients.copy()
		self.__clients_sema.release()
		for client_addr, client in clients.items():
			client.disconnect()
		if self.on_disconnect != None: self.on_disconnect()
		self.stop()

	# Disconnect a client.
	def disconnectClient(self, client):
		self.__clients_sema.acquire()
		if  self.__clients.has_key(client.addr): del self.__clients[client.addr]
		self.__clients_sema.release()
		if self.verbose:
			print "Disconnect client %s:%u" % (client.host, client.port)
		if self.on_client_disconnect != None: self.on_client_disconnect (client)
		if self.__server == client: self.disconnect()
	
	# Send a packet to the server or to all clients
	def send(self, packet, to=None):
		if not self.__running: return
		
		# Read binary version of the packet
		data = packet.pack()

		if self.__is_server:
			if to==None:
				self.__clients_sema.acquire()
				clients = self.__clients.copy()
				self.__clients_sema.release()	
				for client in clients:
					client.sendBinary(data)
			else:
				to.sendBinary(data)
		else:
			self.__server.sendBinary(data)

	# Keep the connection alive
	def live(self):				
		clients = self.clients
		for client_addr, client in clients.items():
			data = client.receiveNonBlocking()
			if data != None:
				self.__processData(client, data)

	def __processData(self, client, data):
		while data != "":
			packet = io.Packet()
			packet.recv_from = client
			data = packet.unpack(data)
			if not packet.isValid():
				print "Bad data packet (%s) from %s !" % (data, client.name)
				return
			if self.debug: print "Received %s:%u => \"%s\"" % (client.host, client.port, packet.data)
			if self.on_new_packet: self.on_new_packet(packet)
	
	# Function which should be called in a thread
	def run_thread(self):
		try:
			while self.__running:
				self.live()				
				time.sleep(self.thread_sleep)
		except Exception, msg:
			print "EXCEPTION DANS LE THREAD IO :"
			print msg
			traceback.print_exc()
			self.stop()

	def stop(self):
		if not self.__running: return
		self.__running = False
		self.disconnect()

	def isRunning(self): return self.__running

	#--- Private functions ------------------------------------------------------

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
	
	def clientConnect(self, client):
		client.on_receive = self.on_receive
		client.on_send = self.on_send
		self.__clients_sema.acquire()
		self.__clients[client.addr] = client
		self.__clients_sema.release()
		if self.on_client_connect != None: self.on_client_connect (client)
		
	def clientDisconnect(self, client):
		if self.debug:
			print "Client %s leave server %s." \
				% (client.name, self.name)
		self.__clients_sema.acquire()
		self.__clients.remove(client)
		self.__clients_sema.release()
		self.__waiter.client_disconnect(client)
		if self.on_client_disconnect != None: self.on_client_disconnect (client)
		
	#--- Properties -------------------------------------------------------------

	name = property(__getName, __setName)
	addr = property(__getAddr)
	port = property(__getPort)
	host = property(__getHost)
	clients = property(__getClients)
	max_clients = property(__getMaxClients)
