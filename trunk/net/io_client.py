import socket

class IO_Client(object):
	def __init__(self, io, addr, name=None, conn=None):
		self.__addr = addr
		self.name = name
		self.__io = io
		if self.name == None:
			self.name = "%s:%u" % (self.host, self.port)

		# TCP
		self.conn = conn
		self.connected = False
		self.net_server = None

	# TCP
	def connect(self, server):
		self.net_server = server
		self.connected = True

	def send(self, packet):
		if self.conn != None:
			self.conn.send(packet.pack())
		else:
			self.__io.send(packet, to=self)

	def receiveNonBlocking(self, max_size=1024):
		try:
			self.conn.setblocking(0)
			return self.conn.recv(max_size)
		except socket.error, err:
			if err[0] == 11: return None
			raise

	def receiveBlocking(self, max_size=1024):
		self.conn.setblocking(1)
		return self.conn.recv(max_size)

	# TCP
	def disconnect(self):
		if self.conn != None: self.conn.close()
		self.__io.disconnectClient(self)

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
