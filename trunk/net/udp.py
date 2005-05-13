#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

import time
import thread
import socket
import sys
import traceback
import re

class Packet(object):
	timeout = 0.100
	max_resend = int(10.000 / timeout)
	
	def __init__(self, data=None):
		self.sent = 0
		self.__data = None
		self.timeout = None
		self.skippable = False
		self.id = None
		self.unpack(data)

	def isValid(self):
		return self.__data != None
		
	def toStr(self):
		return "\"%s\" [id=%u, skippable=%u]" \
			% (self.__data, self.id, self.skippable)

	def unpack(self, data):
		if data==None: return
		m = re.compile("^([0-9]+):([0-9]+):(.+)$").match(data)
		if m == None: return
		self.skippable = (m.group(1) == '1')
		self.id = int(m.group(2))
		self.__data = m.group(3)

	def pack(self):
		return "%u:%u:%s" \
			% (self.skippable, self.id, self.__data)
		
	def writeStr(self, str):
		if self.__data == None:
			self.__data = str
		else:
			self.__data = self.__data + str
			
	def prepareSend(self):
		self.timeout = time.time()+Packet.timeout
		self.sent = self.sent + 1

	def getData(self): return self.__data
	data = property(getData)	

class IO_UDP:
	def __init__(self, is_server=False):
		self.debug = False
		self.packet_timeout = 1.000
		self.__socket = None
		self.__addr = None
		self.__packet_id = 0
		self.__is_server = is_server
		self.__clients = []
		self.__waitAck = {}
		self.thread_receive = True
		self.thread_sleep = 0.010

	def connect(self, host, port):
		self.__addr = (host, port,)
		self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		if self.__is_server:
			print "Run server at %s:%u" % (self.__addr[0], self.__addr[1])
			self.__socket.bind(self.__addr)
		else:
			print "Connect to server %s:%u" % (self.__addr[0], self.__addr[1])			
		self.__socket.setblocking(0)
	
	def send(self, packet):
		if self.__is_server and len(self.__clients)==0: return
		
		# Prépare le paquet à l'envoi
		packet.prepareSend()
		if packet.sent == 1:
			self.__packet_id = self.__packet_id + 1
			packet.id = self.__packet_id
			if self.debug: packet.creation = time.time()
			if not packet.skippable:				
				self.__waitAck[packet.id] = packet
				
		data = packet.pack()
		if self.debug:
			t = time.time() - packet.creation
			print "Send data : \"%s\" (time=%.1f ms)." % (data, 1000*t)

		if self.__is_server:
			for client in self.__clients:
				self.__socket.sendto(data, client)
		else:
			self.__socket.sendto(data, self.__addr)

	def connectClient(self, addr):
		self.__clients.append(addr)
		print "New client : %s:%u" % (addr[0], addr[1])

	def processAck(self, id):
		if self.__waitAck.has_key(id):			
			if self.debug:
				t = time.time() - self.__waitAck[id].creation
				print "Ack %u received (time=%.1f ms)" % (id, t*1000)
			del self.__waitAck[id]
		else:
			if self.debug: print "No more packet %u" % (id)

	def receive(self, max_size = 1024):
		try:						
			data,addr = self.__socket.recvfrom(max_size)
		except socket.error, err:
			if err[0] == 11: return None
			raise

		if self.debug: print "Received packet (\"%s\" from %s:%u)" % (data, addr[0], addr[1])
		
		# Le message provient d'un nouveau client ?
		if self.__is_server:
			if addr not in self.__clients:
				self.connectClient(addr)

		# Si c'est un accusé de réception, le prend en compte
		m = re.compile("^ACK ([0-9]+)$").match(data)
		if m != None:
			self.processAck(int(m.group(1)))
			return None

		# Traduit les données binaires en paquet	
		packet = Packet(data)
		if not packet.isValid(): return None
		
		# Envoie un accusé de réception si nécessaire
		if not packet.skippable: self.__sendAck(packet, addr)
		return packet

	def __sendAck(self, packet, addr):
		data = "ACK %u" % (packet.id)
		if self.debug: print "Send ACK : \"%s\"." % (data)
		self.__socket.sendto(data, addr)

	def live(self):				
		for id in self.__waitAck:
			packet = self.__waitAck[id]
			if packet.timeout < time.time():
				if packet.sent < Packet.max_resend:
					self.send(packet)
				else:
					raise Exception, "Paquet envoyé plus de %u fois !" % (Packet.max_resend)		
					
	def run_thread(self):
		try:
			while 1:
				self.live()				
				if self.thread_receive:
					packet = self.receive()				
					if packet != None:
						print "Received : %s" % (packet.toStr())
				time.sleep(self.thread_sleep)
		except Exception, msg:
			print "EXCEPTION DANS LE THREAD IO :"
			print msg
			print "--"			
			traceback.print_exc()

def loop_server(io):
	io.thread_sleep = 0.001
	thread.start_new_thread( io.run_thread, ())
	while 1:
		msg = raw_input(">> ")
		if msg=="": break
		packet = Packet()
		packet.writeStr(msg)
		io.send(packet)
		time.sleep(0.100)
		print ""
		
def loop_client(io):
	io.thread_receive = False
	thread.start_new_thread( io.run_thread, ())
	
	while 1:
		msg = raw_input(">> ")
		if msg=="": break
		
		m = re.compile("^eval:(.+)$").match(msg)
		if m != None: msg = eval(m.group(1))			
		
		packet = Packet()
		packet.writeStr(msg)
		if msg[0]=='0':			
			packet.skippable = True
		io.send(packet)
		io.thread_receive = True
		time.sleep(0.100)
		print ""

def main():
	is_server = False
	for arg in sys.argv[1:]:
		if arg=="--server": is_server = True
	io = IO_UDP(is_server)
	io.debug = True
#	port = 12430
	port = 1080
	if is_server:
		host = ''
	else:
		host = 'localhost'
#		host = 'tchoy.net'
		host = '10.20.0.117'
	io.connect(host, port)	
	
	if is_server:
		loop_server(io)
	else:
		loop_client(io)
	
if __name__=="__main__": main()
