from net import net_client
import common

class ClientIO:
	def __init__(self):
		self.client = None
		self.on_write = None
		self.on_read = None
		self.client = net_client.NetworkClient()

	def setVerbose(self, verbose):
		self.client.verbose = verbose

	def start(self, host, port):
		self.client.connect(host, port)
		
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
		self.client.disconnect()

	def getPort(self):
		return self.client.port
	port = property(getPort,)

	def getHost(self):
		return self.client.host
	host = property(getHost,)
