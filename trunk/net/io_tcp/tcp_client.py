from net import io
import socket

class TCP_Client(io.IO_Client):
	def __init__(self, io_tcp, addr, name=None, socket=None):
		io.IO_Client.__init__(self, io_tcp, addr, name)
		self.__socket = socket 
		self.on_send = None
		self.on_receive = None

	def send(self, packet):
		self.sendBinary( packet.pack() )
	
	def sendBinary(self, data):
		if not self.connected: return
		self.__socket.send(data)

		# Call user event if needed
		if self.on_send != None: self.on_send(data)

	def receiveNonBlocking(self, max_size=1024):
		if not self.connected: return
		try:
			self.__socket.setblocking(0)
			data = self.__socket.recv(max_size)
		except socket.error, err:
			if err[0] == 11: return None
			# Broken pipe (32) or Connection reset by peer (104)
			if err[0] in (32, 104,):
				self.disconnect()
				return None
			raise
		return self.__processRecvData(data)

	def receiveBlocking(self, max_size=1024):
		if not self.connected: return
		try:
			self.__socket.setblocking(1)
			data = self.__socket.recv(max_size)
		except socket.error, err:
			# Broken pipe (32) or Connection reset by peer (104)
			if err[0] in (32, 104,):
				self.disconnect()
				return None
			print err
			raise
		return self.__processRecvData(data)

	def disconnect(self):
		self.__socket.close()
		io.IO_Client.disconnect(self)

	def __processRecvData(self, data):
		# If no data, connection is lost
		if len(data)==0:
			if self.io.verbose:
				print "Client %s lost connection with server!" % (self.name)
			self.disconnect()
			return None

		# Call user event if needed
		if self.on_receive != None: self.on_receive(data)
		return data
