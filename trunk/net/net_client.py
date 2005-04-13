from socket import *
import common

class NetworkClient:
	def __init__(self, host, port):
		self.HOST = host
		self.PORT = port
		print "Connect to %s:%s." % (self.HOST, self.PORT)
		self.s = socket(AF_INET, SOCK_STREAM)

	def connect(self):
		print "Start client."
		self.s.connect((self.HOST, self.PORT))

	def send(self, data):
		self.s.send(data)

	def readNonBlocking(self, max_size=1024):
		self.s.setblocking(0)
		try:
	 		data = self.s.recv(max_size) 
		except:
			return None
		if len(data)==0: return None
		return data

	def stop(self):
		self.s.close()
