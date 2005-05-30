import socket
import time

class ClientBuffer:
	def __init__(self):
		self.max_time = 0.010
		self.max_size = 2
		self.__time = time.time()
		self.__reset()

	def __reset(self):
		self.__size = 0
		self.__buffer = ""

	def __shouldBeSend(self):
		if self.max_size <= self.__size:
			print "buffer full (size=%s)" % (self.__size)
			return True
		diff = time.time() - self.__time
		if self.max_time <= diff:
			print "net timeout -> send (size=%s/%s)." \
				% (self.__size, self.max_size)
			return True
		return False

	def getMsg(self):
		if self.__size==0: return None
		if not self.__shouldBeSend(): return None
		buf = self.__buffer
		self.__reset()
		return buf

	def addMsg(self, msg, urgent):
		if self.__size==0:
			self.__time = time.time()
		self.__buffer += msg
		self.__size = self.__size + 1
		if urgent or self.__shouldBeSend():
			buf = self.__buffer
			print "Do send."
			self.__reset()
			return buf 
		return None

class NetworkServerClient(object):
	def __init__(self, conn, addr):
		self.conn = conn
		self.addr = addr
		self.net_server = None
		self.connected = False
		self.on_read = None
		self.on_send = None
		self.__name = None
		self.__buffer = ClientBuffer()
		self.__buffer.max_size = 10
		self.__buffer.max_time = 0.010

	def live(self):
		msg = self.__buffer.getMsg()
		if msg!=None: self.__send(msg)
		
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
		
	def send(self, data, urgent=False):
		if not self.connected: return
		
		data = self.__buffer.addMsg(data, urgent)
		if data== None: return

		self.__send(data)

	def __send(self, data):
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
