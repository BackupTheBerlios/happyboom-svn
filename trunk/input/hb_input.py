from common import io
import socket
import thread

class Reader:
	def __init__(self):
		self.on_input = None

	def kill(self):
		thread.exit()

	def loop(self):
		while 1:
			cmd = raw_input("cmd ? ")
			if self.on_input != None: self.on_input(cmd)
			

class Input:
	def __init__(self):
		self.io = io.ClientIO()
		self.cmd_ok = ("quit", "+", "-")
		self.reader = None
		self.quit = False
		self.active = True
		self.debug = False
		self.verbose = False
		self.cmds = None
		self.__protocol_version = "0.1.4"

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
		return True

	def start(self, host, port):
		# Try to connect to server
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
		self.reader = Reader()
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

	def on_disconnect(self, lost_connection):
		if lost_connection == True: 
			print "Lost connection with server :-("
		self.stop()

	def stop(self):
		if not self.active: return
		self.quit = True
		if self.reader != None: self.reader.kill()
		self.io.stop()
		self.active = False
		print "Input closed."


