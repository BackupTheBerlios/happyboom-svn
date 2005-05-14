from io_client import IO_Client

class TCP_Client(IO_Client):
	def __init__(self, io, addr, name=None, conn=None):
		IO_Client.__init__(self, io, addr, name)
		self.conn = conn
		self.connected = False
		self.net_server = None

	def setNetServer(self, server):
		self.net_server = server
		self.connected = True

	def send(self, packet):
		self.conn.send(packet.pack())

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
		self.conn.close()
		IO_Client.disconnect(self)
