from net import io
import threading
import time
from udp_ping import UDP_Pinger 

class UDP_Client(io.IO_Client):
	def __init__(self, io_udp, addr, name=None):
		io.IO_Client.__init__(self, io_udp, addr, name)
		self.send_ping = False
		self.__waitAck = {}
		self.__received = {}
		self.__waitAck_sema = threading.Semaphore()
		self.__received_sema = threading.Semaphore()
		self.__pinger = UDP_Pinger(self)

	def alreadyReceived(self, id):
		self.__received_sema.acquire()
		received = id in self.__received
		self.__received_sema.release()
		return received

	def receivePacket(self, packet):
		if packet.skippable: return
		
		# Store packet to drop packet which are receive twice
		timeout = time.time()+io.Packet.total_timeout
		self.__received_sema.acquire()
		self.__received[packet.id] = timeout 
		self.__received_sema.release()	

	def processPing(self, id):
		self.__pinger.processPing(id)
		
	def processPong(self, id):
		self.__pinger.processPong(id)
		
	def processAck(self, id):
		self.__waitAck_sema.acquire()
		if not self.__waitAck.has_key(id):
			self.__waitAck_sema.release()
			return

		# Debug message
		if self.io.debug:
			t = time.time() - self.__waitAck[id].creation
			print "Ack %u received (time=%.1f ms)" % (id, t*1000)

		# The packet don't need ack anymore
		del self.__waitAck[id]
		self.__waitAck_sema.release()

	def disconnect(self):
		self.io.disconnectClient(self)

	def needAck(self, packet):
		self.__waitAck_sema.acquire()
		self.__waitAck[packet.id] = packet
		self.__waitAck_sema.release()

	def live(self):
		# Resend packet which don't have received their ack yet
		self.__waitAck_sema.acquire()
		waitAckCopy = self.__waitAck.copy()
		self.__waitAck_sema.release()
		for id,packet in waitAckCopy.items():
			if packet.timeout < time.time():
				if packet.sent < io.Packet.max_resend:
					self.send(packet)
				else:
					self.io.clientLostConnection(self)

		# Clean old received packets 
		self.__received_sema.acquire()
		receivedCopy = self.__received.copy()
		self.__received_sema.release()
		for id,timeout in receivedCopy.items():
			if timeout < time.time():
				if self.io.debug:
					print "Supprime ancien paquet %u de %s:%u (timeout)" \
						% (id, self.host, self.port)
				self.__received_sema.acquire()
				del self.__received[id]
				self.__received_sema.release()

		# Send ping if needed
		if self.send_ping: self.__pinger.live()

	# Send packet
	def send(self, packet):
		self.io.send(packet, to=self)
		
	# Send binary data
	def sendBinary(self, data):
		self.io.sendBinary(data, self)
