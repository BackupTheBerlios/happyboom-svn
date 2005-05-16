import time
import struct
from net import io

class UDP_Ping:
	timeout = 3.000
	
	def __init__(self, id):
		self.creation = time.time()
		self.timeout = self.creation+UDP_Ping.timeout
		self.id = id

	def getPacket(self):
		ping = io.Packet()
		ping.type = io.Packet.PACKET_PING
		ping.writeStr( struct.pack("!I", self.id) )
		return ping	

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
		self.client.send( ping.getPacket() )
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

	def __getPingId(self, data):
		format  = "!I"
		if len(data) != struct.calcsize(format): return None
		data = struct.unpack(format, data)
		return data[0]

	def processPing(self, packet):
		pong = io.Packet(skippable=True)
		pong.type = io.Packet.PACKET_PONG
		pong.writeStr( packet.data )
		self.client.send(pong)
		
	def processPong(self, packet):
		id = self.__getPingId(packet.data)
		if id == None:
			if self.debug:
				print "Wrong ping packet (%s)!" % (packet.toStr())
			return

		# Received too late ?
		if not self.__sent_ping.has_key(id): return

		# Remove ping from the list
		del self.__sent_ping[id]
