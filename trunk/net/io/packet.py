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
	def __init__(self, str=None, skippable=False):
		self.sent = 0
		self.__data = None
		self.timeout = None
		self.skippable = skippable
		self.id = None
		self.recv_from = None
		if str != None: self.writeStr(str)

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

		if False: #self.id == None:
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
			format = "!BII"
			size = struct.calcsize(format)
			if len(binary_data) <  size:
				print "Taille du paquet (%s) incorrect !" % (binary_data)
				return None
			data = struct.unpack(format, binary_data[:size])
			self.skippable = (data[0]==1)
			self.id = data[1]
			data_len = data[2]
			binary_data = binary_data[size:]

		# Read data
		format = "!%us" % (data_len)
		size = struct.calcsize(format)
		if len(binary_data) < size:
			print "Taille du paquet (%s) incorrect !" % (binary_data)
			return None
		
		data = struct.unpack(format, binary_data[:size]) 
		self.__data = data[0] 
		return binary_data[size:]

	# Pack datas to a binary string (using struct module)
	def pack(self):
		data_len = len(self.__data)
		if self.id == None:
			return struct.pack("!I%us" % data_len, 
				data_len, self.__data)
		else:
			return struct.pack("!BII%us" % data_len, 
				self.skippable+0, self.id, data_len, self.__data)
		
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


