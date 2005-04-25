from common import io
import socket
import thread
import time
import string
import os
import signal

class PingClient:
	def __init__(self, server):
		self.server = server 
		self.next_ping = time.time()
		self.ping_time = None
		self.ping_pause = 1.0
		self.ping_timeout = 2.0
		self.quit = False

	def stop(self):
		if self.quit: return
		self.quit = True
		if self.server.active:
			os.kill(self.server.pid, signal.SIGINT)

	def run(self):
		try:
			while 1:
				self.one_loop()
				if self.quit: break
				time.sleep(0.100)
		except Exception, msg:
			print "PING CLIENT EXCEPTION:"
			print msg
			self.stop()

	def one_loop(self):
		if self.ping_time != None:
			if self.ping_timeout < time.time() - self.ping_time:
				print "Server don't answer :-P"
				self.stop()
				return
				
			pong = self.server.io.read(10)
			if pong != None:
				#if self.server.debug:
			#		diff = time.time() - self.ping_time
				#	print "Responce to ping after %u ms: %s" \
				#		% (int(diff * 1000), pong[0])
				self.ping_time = None
				self.next_ping = time.time() + self.ping_pause
		else:
			if self.next_ping < time.time():
#				if self.server.debug: print "Send ping."
				self.ping_time = time.time()
				self.server.sendCmd("Ping?")

class BaseInput(object):
	def __init__(self):
		self.io = io.ClientIO()
		self.pid = os.getpid()
		self.ping = PingClient(self)
		self.quit = False
		self.active = True
		self.debug = False
		self.verbose = False
		self.cmds = None
		self.use_readline = False
		self.__protocol_version = "0.1.4"
		self.name = "-"

	def readCmd(self, max_len=512):
		if self.cmds != None:
			answer = self.cmds[0]
			del self.cmds[0]
			if len(self.cmds)==0: self.cmds = None
		else:
			lines = self.io.readBlocking()
			if lines == None: return None
			if len(lines)==0:
				if self.debug: print "Empty answer !?"
				return None
			if 1<len(lines):
				self.cmds = lines[1:]
			answer = lines[0]
		if max_len < len(answer): answer = answer[:max_len]
		return answer

	def serverChallenge(self):
		if self.verbose: 
			print "Start server challenge (send version, send name, ...)."

		cmd = self.readCmd(50)
		if cmd != "Version?": 
			if self.debug: print "Server answer: %s instead of Version?" % (cmd)
			return False
		self.sendCmd(self.__protocol_version)
		
		cmd = self.readCmd(10)
		if cmd != "OK":
			if self.debug: print "Server answer: %s instead of OK" % (cmd)
			return False
		
		cmd = self.readCmd(50)
		if cmd != "Name?":
			if self.debug: print "Server answer: %s instead of Name?" % (cmd)
			return False
		self.sendCmd(self.name)

		if self.debug: print "Challenge: Wait Name OK"
		cmd = self.readCmd(10)
		if cmd != "OK":
			if self.debug: print "Server answer: %s instead of OK" % (cmd)
			return False
		if self.verbose: print "Server challenge done."
		return True

	def start(self, host, port):
		# Try to connect to server
		if self.verbose: 
			print "Try to connect to server %s:%s" % (host, port)
		self.io.on_disconnect = self.on_disconnect
		ok = self.io.start(host, port)
		if not ok:
			print "Connection to server %s:%u failed (too many connections ?) !" \
				% (host, port)
			self.stop()
			return

		# Server "challenge" (version, name, ...)
		if self.serverChallenge() != True:
			print "Server communication mistake !?"
			self.stop()
			return

		# Start ping thread
		thread.start_new_thread( self.ping.run, ())

	def setDebugMode(self, debug):
		self.io.setDebug(debug)
		self.debug = debug

	def setVerbose(self, verbose):
		self.verbose = verbose

	def sendCmd(self, cmd):
		self.io.send(cmd+"\n")

	def processCmd(self, cmd):
		if cmd != "": self.sendCmd(cmd)

	def live(self):
		if self.use_readline: import readline
		while self.quit == False:
			cmd = raw_input("cmd ? ")
			cmd = string.strip(cmd)
			if cmd != "":
				self.processCmd(cmd)
			if self.io.connected == False:
				self.quit = True
			if (cmd == "quit") or (cmd == "close"):
				self.quit = True

	def on_disconnect(self, lost_connection):
		if lost_connection == True: 
			print "Lost connection with server :-("
		self.ping.stop()

	def stop(self):
		if not self.active: return
		self.active = False
		self.quit = True
		if self.ping != None:
			self.ping.stop()
		self.io.stop()
		print "Input closed."


