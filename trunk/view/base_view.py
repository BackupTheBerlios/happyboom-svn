from common import io
from view_agent_manager import *
from common import mailing_list
import socket

class BaseView(object):
	instance = None

	def __init__(self):
		BaseView.instance = self
		self.io = io.ClientIO()
		self.n = None
		self.agents = {}
		self.loop = True
		self.clear_screen = True
		self.mailing_list = mailing_list.MailingList()
		self.on_recv_message = None
		self.verbose = False
		self.stats = False
		self.debug = False
		self.max_fps = 25
		self.server_timeout = 10.0
		self.wait_server_time = None
		self.__protocol_version = "0.1.4"
		self.name = "no name"
		self.active = True
		self.only_watch_server = False

	def getAgent(self, id):
		return self.agents.get(id, None)

	def registerAgent(self, id, agent):
		agent.id = id
		agent.server = self
		self.agents[id] = agent
		agent.start()

	def start(self, host, port):
		if self.verbose: print "Try to connect to server %s:%u." \
			% (host, port)
		self.io.on_connect = self.on_connect
		self.io.on_disconnect = self.on_disconnect
		if not self.io.start(host, port):
			print "Connection to server %s:%s failed !" % (self.io.host, self.io.port)
			self.loop = False

	def on_connect(self):
		if self.verbose: print "Connected to server."

	def on_disconnect(self, lost_connection):
		if lost_connection == True: 
			print "Connection with server broken :-("
		elif self.verbose:
			print "Connection to server closed."
		self.loop = False

	def str2msg(self, str):
		import re
		# Ugly regex to parse string
		r = re.compile("^([^:]+):([^:]+)(:(.*))?$")
		regs = r.match(str)
		if regs == None: return None
		
		role = regs.group(1)
		type = regs.group(2)
		if 2<regs.lastindex:
			arg = regs.group(4)
		else:
			arg = None
		return AgentMessage(role, type, arg)

	def registerMessage(self, agent, role):
		self.mailing_list.register(role, agent)
	
	def processMessages(self, lines):
		for line in lines:
			msg = self.str2msg(line)
			if msg != None: 
				if self.debug: print "Received message: %s" %(msg.str())
				if self.on_recv_message: self.on_recv_message (msg)
				locals = self.mailing_list.getLocal(msg.role)
				for agent in locals: agent.putMessage(msg)

	def send(self, str):
		self.io.send(str+"\n")
	
	def live(self):
		if not self.io.connected:
			if self.verbose or (self.wait_server_time == None):
				print "Waiting for connection to server ..."
			if self.wait_server_time != None:
				if self.server_timeout < time.time() - self.wait_server_time:
					print "Server %s:%u doesn't answer, try again." \
						% (self.io.host, self.io.port)
					self.stop()
					return
			else:
				self.wait_server_time = time.time()
			time.sleep(1.0)
			return
	
		live_begin = time.time()

		# Do a copy because agent manager can add new agent, and Python
		# forbid to modify a list during a "for x in <list>"
		agents_list = self.agents.copy()
		
		# Call live() function for each agent
		for key in agents_list:
			agent = agents_list[key]
			agent.live()
	
		# Read messages from server
		lines = self.io.read()
		if lines!=None: self.processMessages(lines)

		# Draw the screen
		self.draw()
		
		# Sleep to limit CPU consomation
		delay = time.time() - live_begin
		frame_time = 1.0 / self.max_fps
		if delay < frame_time:
			delay = frame_time - delay
			time.sleep(delay)
			
	def draw(self):
		pass
		
	def setDebugMode(self, debug):
		self.debug = debug
		self.io.setDebug(debug)

	def setVerbose(self, verbose):
		self.verbose = verbose
		self.clear_screen = not verbose

	def stop(self):
		if not self.active: return
		self.active = False
		self.loop = False
		self.io.send("quit")
		self.io.stop()
		print "View closed."

	def getProtocolVersion(self):
		return self.__protocol_version
	protocol_version = property(getProtocolVersion)
