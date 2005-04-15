from net import net_client
import common

class ClientIO:
	def __init__(self):
		self.on_write = None
		self.on_read = None
		self.on_connect = None  # No argument
		self.on_disconnect = None  # Have one arg : lost_connection
		self.__client = net_client.NetworkClient()

	# Try to connect to host:port
	# Return False if an error occurs, True else
	def start(self, host, port):
		self.__client.on_connect = self.on_connect
		self.__client.on_disconnect = self.on_disconnect
		return self.__client.connect(host, port)

	def setDebug(self, debug):
		self.__client.debug = debug

	def send(self, data):
		self.__client.send(data)
		if self.on_write != None: self.on_write (data)
	
	def __processRead(self, data):
		if data==None: return None
		if self.on_read != None: self.on_read (data)
		lines = data.split("\n")
		for line in lines:
			if line=="": lines.remove(line)
		return lines

	def readBlocking(self, max_size=512):
		data = self.__client.readBlocking(max_size)
		return self.__processRead(data)

	def read(self, max_size=512):
		data = self.__client.readNonBlocking(max_size)
		return self.__processRead(data)
		
	def stop(self):
		self.__client.disconnect()

	def getPort(self):
		return self.__client.port
	port = property(getPort,)

	def getConnected(self):
		return self.__client.connected
	connected = property(getConnected,)
	
	def getHost(self):
		return self.__client.host
	host = property(getHost,)
