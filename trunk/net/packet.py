import time
import struct

class Packet(object):
	# Timeout before packet is resend
	timeout = 0.250

	# Timeout before packet is said to be "lost"
	total_timeout = 3.000 

	# Maximum number of packet resend
	max_resend = int(3.000 / timeout)
	
	# Constructor
	# data (optionnal) is a binary packet
	def __init__(self, data=None):
		self.sent = 0
		self.__data = None
		self.timeout = None
		self.skippable = False
		self.id = None
		self.unpack(data)

	# After unpack, say if the packet is valid or not
	def isValid(self):
		return self.__data != None
		
	# For debug only, convert to string
	def toStr(self):
		return "\"%s\" [id=%u, skippable=%u]" \
			% (self.__data, self.id, self.skippable)

	# Fill attributs from a binary data packet
	def unpack(self, binary_data):
		if binary_data==None: return

		# Read skippable, id, data len
		format = "!BII"
		size = struct.calcsize(format)
		if len(binary_data) <  size: return None
		data = struct.unpack(format, binary_data[:size])
		self.skippable = (data[0]==1)
		self.id = data[1]
		data_len = data[2]
		binary_data = binary_data[size:]

		# Read data
		format = "!%us" % (data_len)
		if len(binary_data) != struct.calcsize(format): return None
		
		data = struct.unpack(format, binary_data) 
		self.__data = data[0] 

	# Pack datas to a binary string (using struct module)
	def pack(self):
		data_len = len(self.__data)
		return struct.pack("!BII%us" % data_len, 
			self.skippable,	self.id, data_len, self.__data)
		
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


