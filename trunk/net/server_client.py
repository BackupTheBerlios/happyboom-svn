import socket
import time

class NetworkServerClient(object):
	def __init__(self, conn, addr):
		self.conn = conn
		self.addr = addr
		self.net_server = None
		self.connected = False
		self.on_read = None
		self.on_send = None
		self.__name = None

	def getName(self):
		if self.__name != None: return self.__name
		return "{ip=%s port=%u}" % (self.addr[0], self.addr[1])
	def setName(self, name):
		self.__name = name
	name = property(getName,setName)
	
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
		except socket.error, err:
			if err[0] == 11:
				return None
			# Broken pipe (32) or Connection reset by peer (104)
			if err[0] in (32, 104,):
				self.disconnect()
				return None
			raise
		if len(data)==0:
			if self.net_server.debug:
				print "Server %s lost connection with client %s !" \
					% (self.net_server.name, self.name)
			self.disconnect()
			return None
		if self.on_read != None: self.on_read(data)
		return data

	def read(self, max_size=1024, timeout=3000):
		if not self.connected: return None
		loop = True 
		start = time.time()
		while loop:
			try:
	 			data = self.conn.recv(max_size) 
				loop = False
			except socket.error, err:
				if err[0] == 11:
					if timeout < (time.time() - start)*1000:
						return None
					time.sleep(0.001)
				# Broken pipe (32) or Connection reset by peer (104)
				elif err[0] in (32, 104,):
					self.disconnect()
					return None
				else:
					raise
		if len(data)==0:
			if self.net_server.debug:
				print "Server %s lost connection with client %s !" \
					% (self.net_server.name, self.name)
			self.disconnect()
			return None
		if self.on_read != None: self.on_read(data)
		return data

	def send(self, data):
		if not self.connected: return
		try:
			self.conn.send(data)
		except socket.error, err:
			# Broken pipe (32) or Connection reset by peer (104)
			if err[0] in (32, 104,):
				self.disconnect()
				return
			elif err[0] == 11:
				print "Continue"
				raise
			else:
				print "Other error"
				raise
		if self.on_send != None: self.on_send(data)

	def stop():
		self.conn.close()
