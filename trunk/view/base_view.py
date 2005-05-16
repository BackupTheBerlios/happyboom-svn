from view_agent_manager import *
from common import mailing_list
from net import io
#from net import io_udp
from net import io_tcp
import thread

class BaseView(object):
	instance = None

	def __init__(self):
		BaseView.instance = self
		#self.__io = io_udp.IO_UDP()
		self.__io = io_tcp.IO_TCP()
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

	def setIoSendReceive(self, on_send, on_receive):
		self.__io.on_send = on_send
		self.__io.on_receive = on_receive

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
		self.__io.on_connect = self.onConnect
		self.__io.on_disconnect = self.onDisconnect
		self.__io.on_new_packet = self.processPacket
		self.__io.on_lost_connection = self.onLostConnection
		self.__io.connect(host, port)

		thread.start_new_thread( self.__io.run_thread, ())

	def onConnect(self):
		if self.verbose: print "Connected to server."

	def onDisconnect(self):
		print "Connection to server closed."
		self.stop()

	def onLostConnection(self):
		print "Lost connection with server."
		self.stop()

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
	
	def processPacket(self, new_packet):
		msg = self.str2msg(new_packet.data)
		if msg != None: 
			if self.debug: print "Received message: %s" %(msg.str())
			if self.on_recv_message: self.on_recv_message (msg)
			locals = self.mailing_list.getLocal(msg.role)
			for agent in locals: agent.putMessage(msg)

	def send(self, str):
		p = io.Packet()
		p.writeStr( str )
		self.__io.send(p)
	
	def live(self):
		live_begin = time.time()

		# Do a copy because agent manager can add new agent, and Python
		# forbid to modify a list during a "for x in <list>"
		agents_list = self.agents.copy()
		
		# Call live() function for each agent
		for key in agents_list:
			agent = agents_list[key]
			agent.live()
	
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
		self.__io.debug = debug

	def setVerbose(self, verbose):
		self.verbose = verbose
		self.__io.verbose = verbose
		self.clear_screen = not verbose

	def stop(self):
		if not self.active: return
		self.active = False
		self.loop = False
		self.send("quit")
		self.__io.stop()
		print "View closed."

	def getProtocolVersion(self):
		return self.__protocol_version
	protocol_version = property(getProtocolVersion)
