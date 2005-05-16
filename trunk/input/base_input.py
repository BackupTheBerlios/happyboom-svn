import time
import string
import os
import signal
from net import io
from net import io_udp
#from net import tcp
#from net import packet
import thread

class BaseInput(object):
	def __init__(self):
		self.io = io_udp.IO_UDP() 
		#self.io = tcp.IO_TCP() 
		self.pid = os.getpid()
		self.quit = False
		self.active = True
		self.debug = False
		self.verbose = False
		self.cmds = None
		self.use_readline = False
		self.__protocol_version = "0.1.4"
		self.name = "-"
		self.__recv_buffer = []

	def processPacket(self, new_packet):
		self.__recv_buffer.append(new_packet.data.rstrip())
	
	def readCmd(self):
		while len(self.__recv_buffer)==0:
			if self.quit: return None
			time.sleep(0.010)
		msg = self.__recv_buffer[0]
		del self.__recv_buffer[0]
		return msg
	
	def serverChallenge(self):
		if self.verbose: 
			print "Start server challenge (send version, send name, ...)."

		cmd = self.readCmd()
		if cmd==None: return False
		if cmd != "Version?": 
			if self.debug: print "Server answer: %s instead of Version?" % (cmd)
			return False
		self.sendCmd(self.__protocol_version)
		
		cmd = self.readCmd()
		if cmd==None: return False
		if cmd != "OK":
			if self.debug: print "Server answer: %s instead of OK" % (cmd)
			return False
		
		cmd = self.readCmd()
		if cmd==None: return False
		if cmd != "Name?":
			if self.debug: print "Server answer: %s instead of Name?" % (cmd)
			return False
		self.sendCmd(self.name)

		if self.debug: print "Challenge: Wait Name OK"
		cmd = self.readCmd()
		if cmd==None: return False
		if cmd != "OK":
			if self.debug: print "Server answer: %s instead of OK" % (cmd)
			return False
		if self.verbose: print "Server challenge done."
		return True

	def start(self, host, port):
		# Try to connect to server
		if self.verbose: 
			print "Try to connect to server %s:%s" % (host, port)
		self.io.on_disconnect = self.onDisconnect
		self.io.on_lost_connection = self.onLostConnection
		self.io.on_new_packet = self.processPacket
		self.io.connect(host, port)

		thread.start_new_thread( self.io.run_thread, ())
		thread.start_new_thread( self.io_live, ())

		# Server "challenge" (version, name, ...)
		if self.serverChallenge() != True:
			if not self.quit:
				print "Server communication mistake !?"
			self.stop()
			return

	def setDebugMode(self, debug):
		self.debug = debug
		self.io.debug = debug

	def setVerbose(self, verbose):
		self.verbose = verbose
		self.io.verbose = verbose

	def sendCmd(self, cmd):
		self.io.send( io.Packet(cmd+"\n"))

	def processCmd(self, cmd):
		if cmd != "": self.sendCmd(cmd)

	def io_live(self):
		while 1:
			packets = self.__recv_buffer
			self.__recv_buffer = []
			for cmd in packets:
				if cmd == "quit":
					self.stop()
					break
			time.sleep(0.250)
	
	def live(self):
		if self.use_readline: import readline
		while self.quit == False:
			cmd = raw_input("cmd ? ")
			cmd = string.strip(cmd)
			if cmd != "":
				self.processCmd(cmd)
			if (cmd == "quit") or (cmd == "close"):
				self.quit = True

	def onDisconnect(self):
		print "Disconnect from server."
		self.stop()

	def onLostConnection(self):
		print "Lost connection with server."
		self.stop()

	def stop(self):
		if not self.active: return
		self.active = False
		self.quit = True
		self.io.stop()
		print "Input closed."
