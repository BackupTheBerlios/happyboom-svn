import socket
import common

class NetworkClient:
	def __init__(self):
		self.host = None
		self.port = None
		self.connected = False
		self.on_connect = None
		self.on_disconnect = None
		self.s = None
		self.verbose = False

	def connect(self, host, port):
		if self.verbose: print "Start client."
		self.host = host
		self.port = port
		if self.verbose: print "Connect to %s:%s." % (self.host, self.port)
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.connect((self.host, self.port))
		self.connected = True 
		if self.on_connect != None: self.on_connect()

	def disconnect(self):
		if not self.connected: return
		if self.verbose: print "Disconnect client."
		self.s.close()
		self.connected = False
		if self.on_disconnect != None: self.on_disconnect()
		
	def send(self, data):
		if not self.connected: return
		self.s.send(data)

	def readNonBlocking(self, max_size=1024):
		if not self.connected:
			return None
		self.s.setblocking(0)
		try:
	 		data = self.s.recv(max_size) 
		except socket.error, error:
			if error[0] == 11: return None
			raise
		if len(data)==0:
			print "Lost connexion with server (or too many connexions ?) !"
			self.disconnect()
			return None
		return data
