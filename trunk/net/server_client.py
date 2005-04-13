import socket

class NetworkServerClient:
	def __init__(self, conn, addr):
		self.conn = conn
		self.addr = addr
		self.net_server = None
		self.connected = False

	def getAddrStr(self):
		return "ip=%s, port=%u" % (self.addr[0], self.addr[1])
	
	def connect(self, server):
		self.net_server = server
		self.connected = True
		
	def disconnect(self):
		self.connected = False
		if self.net_server != None:
			self.net_server.client_disconnect(self)
		self.conn.close()
			
	def readNonBlocking(self, max_size=1024):
		if not self.connected: return None
		self.conn.setblocking(0)
		try:
	 		data = self.conn.recv(max_size) 
		except socket.error, error:
			if error[0] == 11: return None
			raise
		if len(data)==0:
			print "Lost connexion with client!"
			self.disconnect()
			return None
		return data

	def read(self, max_size=1024):
		if not self.connected: return None
	 	data = self.conn.recv(max_size) 
		if len(data)==0: return None
		return data

	def send(self, data):
		if not self.connected: return
		try:
			self.conn.send(data)
		except socket.error:
			self.disconnect()

	def stop():
		self.conn.close()
