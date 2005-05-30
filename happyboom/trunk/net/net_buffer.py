import threading
import time

class NetBuffer:
	def __init__(self):
		self.blocking_read_sleep = 0.010
		self.__buffer = {} 
		self.__sema = threading.Semaphore()

	def clear(self, key):
		self.__sema.acquire()
		self.__buffer[key] = [] 
		self.__sema.release()
	
	def append(self, key, data):
		self.__sema.acquire()
		if self.__buffer.has_key(key):
			self.__buffer[key].append(data)
		else:
			self.__buffer[key] = [data]
		self.__sema.release()

	def readNonBlocking(self, key):
		self.__sema.acquire()
		buffer = self.__buffer.get(key, [])
		self.__buffer[key] = []
		self.__sema.release()
		return buffer

	def readBlocking(self, key, timeout):
		data = None
		timeout = time.time()+timeout
		while data == None:
			if timeout < time.time(): break
			self.__sema.acquire()
			if self.__buffer.has_key(key) and len(self.__buffer[key]) != 0:
				data = self.__buffer[key][0]
				del self.__buffer[key][0] 
			self.__sema.release()
			if data == None: time.sleep(self.blocking_read_sleep)
		return data
