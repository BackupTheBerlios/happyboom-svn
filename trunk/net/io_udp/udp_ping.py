import time
import struct

class UDP_Ping:
	timeout = 3.000
	
	def __init__(self, id):
		self.creation = time.time()
		self.timeout = self.creation+UDP_Ping.timeout
		self.id = id

	def getBinary(self):
		return struct.pack("!cI", 'P', self.id)

class UDP_Pinger:
	ping_sleep = 1.000
	
	def __init__(self, client):
		self.__next_ping = time.time()+UDP_Pinger.ping_sleep
		self.__ping_id = 0
		self.client = client
		self.__sent_ping = {}

	def processPong(self, id):
		pass

	def sendPing(self):
		self.__ping_id = self.__ping_id + 1
		ping = UDP_Ping(self.__ping_id)
		self.client.sendBinary( ping.getBinary() )
		self.__sent_ping[ping.id] = ping
				
	def pingTimeout(self, id):
		print "Ping timeout (client %s:%u)." \
			% (self.client.host, self.client.port)
#		print "Disconnect client %s:%u : ping timeout." \
#			% (self.client.host, self.client.port)
#		self.client.disconnect()

	def live(self):
		# Remove old ping
		for id,ping in self.__sent_ping.items():
			if ping.timeout < time.time():
				del self.__sent_ping[id]
				self.pingTimeout(id)
		
		# Send ping if needed
		if self.__next_ping < time.time():
			self.__next_ping = time.time()+UDP_Pinger.ping_sleep
			self.sendPing()

	def processPing(self, id):
		data = struct.pack("!cI", 'p', id)
		self.client.sendBinary( data )
		
	def processPong(self, id):
		# Received too late ?
		if not self.__sent_ping.has_key(id): return

		# Remove ping from the list
		del self.__sent_ping[id]
