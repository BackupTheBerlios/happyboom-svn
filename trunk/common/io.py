from net import net_client
import common

class ClientIO:
	def __init__(self):
		self.client = None
		self.on_write = None
		self.on_read = None

	def start(self, port):
		self.client = net_client.NetworkClient(port)
		self.client.connect()
		
	def send(self, data):
		self.client.send(data)
		if self.on_write != None: self.on_write (data)

	def read(self):
		data = self.client.readNonBlocking()
		if data==None: return None
		if self.on_read != None: self.on_read (data)
		lines = data.split("\n")
		for line in lines:
			if line=="": lines.remove(line)
		return lines
		
	def stop(self):
		self.client.stop()

	def getPort(self):
		return self.client.PORT
	port = property(getPort,)

	def getHost(self):
		return self.client.HOST
	host = property(getHost,)
