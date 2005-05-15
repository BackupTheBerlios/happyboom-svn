from io_client import IO_Client
from packet import Packet
import threading
import time
import struct

class UDP_Ping:
	timeout = 1.000
	
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

	def live(self):
		# Remove old ping
		for id,ping in self.__sent_ping.items():
			if ping.timeout < time.time():
				print "Ping %u timeout." % (ping.id)
				del self.__sent_ping[id]
		
		# Send ping if needed
		if self.__next_ping < time.time():
			self.__next_ping = time.time()+UDP_Pinger.ping_sleep
			self.sendPing()

	def processPing(self, id):
		data = struct.pack("!cI", 'p', id)
		self.client.sendBinary( data )
		
	def processPong(self, id):
		if self.__sent_ping.has_key(id):
			ping = self.__sent_ping[id]
			del self.__sent_ping[id]
			t = time.time()-ping.creation
			print "Pong %u (time=%.1f ms)" % (id, t * 1000)
		else:
			print "Pong too late."

class UDP_Client(IO_Client):

	def __init__(self, io, addr, name=None):
		IO_Client.__init__(self, io, addr, name)
		self.waitAck = {}
		self.received = {}
		self.waitAck_sema = threading.Semaphore()
		self.received_sema = threading.Semaphore()
		self.send_ping = False
		self.pinger = UDP_Pinger(self)

	def alreadyReceived(self, id):
		self.received_sema.acquire()
		received = id in self.received
		self.received_sema.release()
		return received

	def receivePacket(self, packet):
		if packet.skippable: return
		
		# Store packet to drop packet which are receive twice
		timeout = time.time()+Packet.total_timeout
		self.received_sema.acquire()
		self.received[packet.id] = timeout 
		self.received_sema.release()	

	def processPing(self, id):
		self.pinger.processPing(id)
		
	def processPong(self, id):
		self.pinger.processPong(id)
		
	def processAck(self, id):
		self.waitAck_sema.acquire()
		if not self.waitAck.has_key(id):
			self.waitAck_sema.release()
			return

		# Debug message
		if self.io.debug:
			t = time.time() - self.waitAck[id].creation
			print "Ack %u received (time=%.1f ms)" % (id, t*1000)

		# The packet don't need ack anymore
		del self.waitAck[id]
		self.waitAck_sema.release()

	def needAck(self, packet):
		self.waitAck_sema.acquire()
		self.waitAck[packet.id] = packet
		self.waitAck_sema.release()

	def live(self):
		# Resend packet which don't have received their ack yet
		self.waitAck_sema.acquire()
		waitAckCopy = self.waitAck.copy()
		self.waitAck_sema.release()
		for id,packet in waitAckCopy.items():
			if packet.timeout < time.time():
				if packet.sent < Packet.max_resend:
					self.send(packet)
				else:
					self.io.clientLostConnection(self)

		# Clean old received packets 
		self.received_sema.acquire()
		receivedCopy = self.received.copy()
		self.received_sema.release()
		for id,timeout in receivedCopy.items():
			if timeout < time.time():
				if self.io.debug:
					print "Supprime ancien paquet %u de %s:%u (timeout)" \
						% (id, self.host, self.port)
				self.received_sema.acquire()
				del self.received[id]
				self.received_sema.release()

		# Send ping if needed
		if self.send_ping: self.pinger.live()

	# Send packet
	def send(self, packet):
		self.io.send(packet, to=self)
		
	# Send binary data
	def sendBinary(self, data):
		self.io.sendBinary(data, self)
