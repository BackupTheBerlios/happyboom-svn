import socket
import common
import time

class NetworkClient(object):
	def __init__(self):
		self.__host = None
		self.port = None
		self.connected = False
		self.on_connect = None # No argument
		self.on_disconnect = None # Have one arg : lost_connection
		self.__socket = None
		self.debug = False
		self.__name = None

	# Try to connect to host:port
	# Return False if an error occurs, True else
	def connect(self, host, port):
		self.__host = host
		self.port = port
		if self.debug: print "Connect to %s:%s." % (self.host, self.port)
		try:
			self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.__socket.connect((self.__host, self.port))
		except socket.error, err:
			if err[0] == 111:
				return False
			print err
			raise
		self.connected = True 
		if self.on_connect != None: self.on_connect()
		return True

	def disconnect(self, lost_connection=False):
		if not self.connected: return
		if self.debug: print "Disconnect client %s." % (self.name)
		self.__socket.close()
		self.connected = False
		if self.on_disconnect != None: self.on_disconnect(lost_connection)
		
	def send(self, data):
		if not self.connected: return
		loop = True
		while loop:
			try:
				self.__socket.setblocking(1)
				self.__socket.send(data)
				loop = False
			except socket.error, err:
				time.sleep(1.0)
				if err[0] in (32, 104):
					if self.debug: print "Lost connection with server (too many connections ?) !"
					self.disconnect(True)
					return
				elif err[0] == 11:
					time.sleep(0.100)
					print "Continue"
				else:
					print "Other error", err
					raise

	def readBlocking(self, max_size=1024):
		if not self.connected:
			return None
		try:
			self.__socket.setblocking(1)
	 		data = self.__socket.recv(max_size) 
		except socket.error, error:
			if error[0] == 11: return None
			raise
		if len(data)==0:
			if self.debug: print "Lost connection with server (too many connections ?) !"
			self.disconnect(True)
			return None
		return data

	def readNonBlocking(self, max_size=1024):
		if not self.connected:
			return None
		try:
			self.__socket.setblocking(0)
	 		data = self.__socket.recv(max_size) 
		except socket.error, error:
			if error[0] == 11: return None
			raise
		if len(data)==0:
			if self.debug: print "Lost connection with server (too many connections ?) !"
			self.disconnect(True)
			return None
		return data

	def getHost(self):
		if self.__host=='': return "localhost"
		return self.__host
	host = property(getHost)

	def getName(self):
		if self.__name != None: return self.__name
		return self.host
	def setName(self, name):
		self.__name = name
	name = property(getName,setName)
