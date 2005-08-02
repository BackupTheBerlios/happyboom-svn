import socket

class IO_Client(object):
	""" IO Client.
	@ivar __addr: Client address (host, port).
	@type __addr: C{(str,int)}
	@ivar connected: Is client connected ?
	@type connected: C{bool}
	@ivar io: Main IO used by client.
	@type io: C{L{BaseIO}}
	@ivar name: Client name.
	@type name: C{str}
	"""
	
	def __init__(self, io, addr, name=None):
		""" Constructor.
		@parameter io: Main IO used by client.
		@type io: C{L{BaseIO}}
		@parameter addr: Client address (host, port).
		@type addr: C{(str,int)}
		@parameter name: Client name.
		@type name: C{str}
		"""
		self.__addr = addr
		self.name = name
		self.connected = True 
		self.io = io
		if self.name == None:
			self.name = "%s:%u" % (self.host, self.port)

	def send(self, packet):
		""" Send a packet to the client.
		@type packet: C{L{Packet}}
		"""
		pass

	def disconnect(self):	
		""" Disconnect the client. """
		self.connected = False
		self.io.disconnectClient(self)

	def __getAddr(self):
		return self.__addr
	def __getHost(self):
		if self.__addr[0]=='': return 'localhost'
		return self.__addr[0]
	def __getPort(self):
		return self.__addr[1]

	addr = property(__getAddr, doc="Client address (host, port)")
	host = property(__getHost, doc="Client network hostname.")
	port = property(__getPort, doc="Client network port.")
