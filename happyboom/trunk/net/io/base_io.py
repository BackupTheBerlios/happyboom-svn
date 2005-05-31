#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

import time
import threading
import socket
import traceback
import struct
from packet import Packet
from io_client import IO_Client

class BaseIO(object):
	def __init__(self, is_server=False):
		self.debug = False
		self.verbose = False 

		# Events
		self.on_connect = None            # No argument
		self.on_lost_connection = None    # No argument
		self.on_disconnect = None         # No argument
		self.on_client_connect = None     # (client)
		self.on_client_disconnect = None  # (client)
		self.on_new_packet = None         # (packet) : client address
		self.on_send = None               # (data)
		self.on_receive = None            # (data)

		self.__name = None

	# Connect to host:port
	def connect(self, host, port):
		if self.__name==None:
			self.__name = "%s:%u" % (host, port)

	# Close connection
	def disconnect(self):
		pass

	# Send a packet to the server or to all clients
	def send(self, packet, to=None):
		pass
	
	# Read a packet from the socket
	# Returns None if there is not new data
	def receive(self, max_size = 1024):
		pass

	# Keep the connection alive
	def live(self):				
		pass

	def disconnectClient(self, client):
		pass
	
	def run_thread(self):
		pass
	
	def stop(self):
		pass

	#--- Private functions ------------------------------------------------------

	def getName(self):
		if self.__name == None: return "no name"
		return self.__name
	
	def setName(self, name):
		self.__name = name	

	#--- Properties -------------------------------------------------------------

	name = property(getName, setName)