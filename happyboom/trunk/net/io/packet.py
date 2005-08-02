"""A network packet. It can have differents types :
1. Data
2. Ping
3. Pong
4. Ack

Ping, pong and ack(nowledge) are only used on transport layer."""
import time
import struct

class Packet(object):
	""" Network packet.
	@ivar id: Packet identifier.
	@type id: C{int}
	@ivar __data: Data string.
	@type __data: C{str}
	@ivar type: Packet type (see types).
	@type type: C{int}
	@ivar recv_from: Packet shipper.
	@type recv_from: C{L{IO_Client}}
	@ivar timeout: Timeout before packet is resend.
	@type timeout: C{float}
	@ivar total_timeout: Timeout before packet is said to be "lost".
	@type total_timeout: C{float}
	@ivar max_resend: Maximum number of packet resend.
	@type max_resend: C{int}
	@ivar use_tcp : Does IO used TCP connection ?
	@type use_tcp: C{bool}
	"""

	timeout = 0.250
	total_timeout = 5.000 
	max_resend = int(total_timeout / timeout)
	use_tcp = False

	# Packet types
	PACKET_DATA = 1
	PACKET_PING = 2
	PACKET_PONG = 3
	PACKET_ACK = 4

	def __init__(self, str=None, skippable=False):
		""" Constructor.
		@parameter str: String data.
		@type str: C{str}
		@parameter skippable: Is the packet skippable if link quality is bad ? See skippable attribute.
		@type skippable: C{bool}
		"""
		self.sent = 0
		self.__data = None
		self.timeout = None
		self.skippable = skippable
		self.id = None
		self.type = Packet.PACKET_DATA
		self.recv_from = None
		self.__valid = True
		if str != None: self.writeStr(str)

	def isValid(self):
		""" After unpack, say if the packet is valid or not.
		@rtype: C{bool}
		"""
		if not Packet.use_tcp and self.id==None: return False
		return self.__valid 
		
	def toStr(self):
		""" For debug only, convert to string """
		if self.type == Packet.PACKET_ACK:
			return "ACK %u [id=%u, skippable=%u]" % (self.id, self.id, self.skippable)
		if self.type == Packet.PACKET_PING:
			ping = struct.unpack("!I", self.__data)
			return "PING %u [id=%u, skippable=%u]" % (ping[0], self.id, self.skippable)
		if self.type == Packet.PACKET_PONG:
			ping = struct.unpack("!I", self.__data)
			return "PONG %u [id=%u, skippable=%u]" % (ping[0], self.id, self.skippable)
		else:
			return "\"%s\" [id=%u, skippable=%u]" \
				% (self.__data, self.id, self.skippable)

	def unpack(self, binary_data):
		""" Fill attributes from a binary data packet
		@parameter binary_data: Binary datas which comes from network.
		@type C{binary}
		"""
		if binary_data==None: return
		self.__valid = False

		if Packet.use_tcp:
			# Read data len
			format = "!I"
			size = struct.calcsize(format)
			if len(binary_data) <  size:
				print "Taille du paquet (%s) incorrect !" % (binary_data)
				return None
			data = struct.unpack(format, binary_data[:size])
			data_len = data[0]
			binary_data = binary_data[size:]
		else:
			# Read skippable, id, data len
			format = "!BBII"
			size = struct.calcsize(format)
			if len(binary_data) <  size:
				print "Taille du paquet (%s) incorrect !" % (binary_data)
				return None
			data = struct.unpack(format, binary_data[:size])
			self.type = data[0]
			self.skippable = (data[1]==1)
			self.id = data[2]
			data_len = data[3]
			binary_data = binary_data[size:]

		# Read data
		if 0 < data_len:
			format = "!%us" % (data_len)
			size = struct.calcsize(format)
			if len(binary_data) < size:
				print "Taille du paquet (%s) incorrect !" % (binary_data)
				return None
			data = struct.unpack(format, binary_data[:size]) 
			self.__data = data[0] 
		else:
			self.__data = None
		self.__valid = True
		return binary_data[size:]

	def pack(self):
		""" Pack datas to a binary string (using struct module)
		@rtype: C{str}
		"""
		if self.__data != None:
			data_len = len(self.__data)
		else:
			data_len = 0
		if Packet.use_tcp:
			data = struct.pack("!I", data_len)
		else:
			data = struct.pack("!BBII", 
				self.type, self.skippable+0, self.id, data_len)
		if data_len != 0:
			data = data + struct.pack("!%us" % data_len, self.__data)
		return data
		
	def writeStr(self, str):
		""" Write a sting into packet (still used ???) """
		if self.__data == None:
			self.__data = str
		else:
			self.__data = self.__data + str
		
	def prepareSend(self):
		""" Prepare the packet before it will be send : set timeout and send counter. """
		self.timeout = time.time()+Packet.timeout
		self.sent = self.sent + 1

	#-- Properties --------------------------------------------------------------

	def getData(self): return self.__data
	data = property(getData, doc="Packet data.")	


