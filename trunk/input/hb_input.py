from common import io
import socket
import thread
import time

class Reader:
	def __init__(self):
		self.on_input = None
		self.use_readline = False
		self.quit = False

	def kill(self):
		self.quit = True
		#thread.exit()
		pass

	def loop(self):
		if self.use_readline: import readline
		try:
			while self.quit == False:
				cmd = raw_input("cmd ? ")
				if self.on_input != None: self.on_input(cmd)
		except KeyboardInterrupt:
			self.kill()

class Input:
	def __init__(self):
		self.io = io.ClientIO()
		self.cmd_ok = ("quit", "+", "-")
		self.reader = Reader()
		self.quit = False
		self.active = True
		self.debug = False
		self.verbose = False
		self.cmds = None
		self.__protocol_version = "0.1.4"
		self.next_ping = time.time()
		self.ping_time = None
		self.ping_pause = 1.0
		self.ping_timeout = 2.0

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
		self.sendCmd(self.io.name)

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

		# Start reader thread
		self.reader.on_input = self.processCmd
		thread.start_new_thread( self.reader.loop, ())

	def setDebugMode(self, debug):
		self.io.setDebug(debug)
		self.debug = debug

	def setVerbose(self, verbose):
		self.verbose = verbose

	def sendCmd(self, cmd):
		self.io.send(cmd+"\n")

	def processCmd(self, cmd):
		if cmd != "": self.sendCmd(cmd)
		if (cmd == "quit") or (cmd == "close"):
			self.stop()

	def live(self):
		if self.io.connected == False:
			self.quit = True
		if self.ping_time != None:
			if self.ping_timeout < time.time() - self.ping_time:
				self.stop()
				return
				
			pong = self.io.read(10)
			if pong != None:
				if self.debug:
					diff = time.time() - self.ping_time
					print "Responce to ping after %u ms: %s" \
						% (int(diff * 1000), pong[0])
				self.ping_time = None
				self.next_ping = time.time() + self.ping_pause
		else:
			if self.next_ping < time.time():
				if self.debug: print "Send ping."
				self.ping_time = time.time()
				self.sendCmd("Ping?")

	def on_disconnect(self, lost_connection):
		if lost_connection == True: 
			print "Lost connection with server :-("
		self.stop()

	def stop(self):
		if not self.active: return
		self.active = False
		self.quit = True
		if self.reader != None:
			self.reader.kill()
		self.io.stop()
		print "Input closed."


