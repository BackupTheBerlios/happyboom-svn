import time
import struct

class Packet(object):
	# Timeout before packet is resend
	timeout = 0.250

	# Timeout before packet is said to be "lost"
	total_timeout = 3.000 

	# Maximum number of packet resend
	max_resend = int(total_timeout / timeout)

	use_tcp = False

	PACKET_DATA = 1
	PACKET_PING = 2
	PACKET_PONG = 3
	PACKET_ACK = 4
	
	# Constructor
	# data (optionnal) is a binary packet
	def __init__(self, str=None, skippable=False):
		self.sent = 0
		self.__data = None
		self.timeout = None
		self.skippable = skippable
		self.id = None
		self.type = Packet.PACKET_DATA
		self.recv_from = None
		self.__valid = True
		if str != None: self.writeStr(str)

	# After unpack, say if the packet is valid or not
	def isValid(self):
		if not Packet.use_tcp and self.id==None: return False
		return self.__valid 
		
	# For debug only, convert to string
	def toStr(self):
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

	# Fill attributs from a binary data packet
	def unpack(self, binary_data):
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

	# Pack datas to a binary string (using struct module)
	def pack(self):
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
		
	# Write a sting into packet
	def writeStr(self, str):
		if self.__data == None:
			self.__data = str
		else:
			self.__data = self.__data + str
		
	# Prepare the packet before it will be send
	def prepareSend(self):
		self.timeout = time.time()+Packet.timeout
		self.sent = self.sent + 1

	#-- Properties --------------------------------------------------------------
	def getData(self): return self.__data
	data = property(getData)	


