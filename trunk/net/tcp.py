#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

import time
import thread
import threading
import socket
import traceback
import struct
from packet import Packet
from tcp_client import TCP_Client
from server_waiter import NetworkServerWaiter
from base_io import BaseIO

class IO_TCP(BaseIO):
	def __init__(self, is_server=False):
		BaseIO.__init__(self)
		self.packet_timeout = 1.000
		self.thread_sleep = 0.010

		self.__is_server = is_server
		self.loop = True

		self.__waiter = NetworkServerWaiter(self)
		self.__socket = None
		self.__socket_open = False		
		self.__addr = None
		self.__clients = {}
		self.__clients_sema = threading.Semaphore()

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
			self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.__socket.connect(self.__addr)
			self.__socket.setblocking(0)

			client = TCP_Client(self, self.__addr, conn=self.__socket)	
			self.__clients_sema.acquire()
			self.__clients[client.addr] = client
			self.__clients_sema.release()

		self.__socket_open = True
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
			print "Disconnect client %s:%u" % (client.host, client.port)
	
	# Send a packet to the server or to all clients
	def send(self, packet, to=None):
		# Read binary version of the packet
		data = packet.pack()

		if self.__is_server:
			if to==None:
				self.__clients_sema.acquire()
				clients = self.__clients.copy()
				self.__clients_sema.release()	
				for client in clients:
					client.send(data)
			else:
				to.send(data)
		else:
			self.__socket.send(data)

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
		return self.__processRecvData(data, addr)

	# Keep the connection alive
	def live(self):				
		clients = self.clients
		for client_addr, client in clients.items():
			data = client.receiveNonBlocking()
			if data != None:
				if len(data)==0:
					client.disconnect()
				else:
					self.__processData(client, data)

	def __processData(self, client, data):
		while data != "":
			packet = Packet(data)
			data = packet.unpack(data)
			packet.recv_from = client
			if self.debug: print "Received %s:%u => \"%s\"" % (client.host, client.port, packet.data)
			if self.on_new_packet: self.on_new_packet(packet)
	
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
		self.__clients_sema.acquire()
		clients = self.__clients.copy()
		self.__clients_sema.release()
		for client_addr, client in clients.items():
			client.conn.close()

		self.loop = False
		self.disconnect()

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
		client.on_read = self.on_read
		client.on_send = self.on_send
		client.setNetServer(self)
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
