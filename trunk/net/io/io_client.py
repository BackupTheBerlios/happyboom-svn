import socket

class IO_Client(object):
	def __init__(self, io, addr, name=None):
		self.__addr = addr
		self.name = name
		self.connected = True 
		self.io = io
		if self.name == None:
			self.name = "%s:%u" % (self.host, self.port)

	def send(self, packet):
		pass

	def disconnect(self):
		self.connected = False
		self.io.disconnectClient(self)

	def __getAddr(self):
		return self.__addr
	def __getHost(self):
		if self.__addr[0]=='': return 'localhost'
		return self.__addr[0]
	def __getPort(self):
		return self.__addr[1]

	addr = property(__getAddr)
	host = property(__getHost)
	port = property(__getPort)
