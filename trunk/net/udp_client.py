from io_client import IO_Client
from packet import Packet
import threading
import time

class UDP_Client(IO_Client):
	ping_sleep = 1.000

	def __init__(self, io, addr, name=None):
		IO_Client.__init__(self, io, addr, name)
		self.waitAck = {}
		self.received = {}
		self.waitAck_sema = threading.Semaphore()
		self.received_sema = threading.Semaphore()
		self.next_ping = time.time()+UDP_Client.ping_sleep
		self.send_ping = False

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
		if self.send_ping and self.next_ping < time.time():
			self.next_ping = time.time()+UDP_Client.ping_sleep
			self.send( Packet("ping") )

	def send(self, packet):
		self.io.send(packet, to=self)
