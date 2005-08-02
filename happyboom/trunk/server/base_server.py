from server_agent import *
from stat import *
from common import mailing_list
import string
import time
import thread
import threading
import random
from net import net_buffer
from net import io
from net import io_udp
#from net import io_tcp
import traceback

class BaseServer(object):
	instance = None
	
	def __init__(self):
		BaseServer.instance = self
		self.agents = []
		self.__view_io = io_udp.IO_UDP(is_server=True)
		self.__input_io = io_udp.IO_UDP(is_server=True)
		#self.__view_io = io_tcp.IO_TCP(is_server=True)
		#self.__input_io = io_tcp.IO_TCP(is_server=True)
		self.__inputs = []
		self.mailing_list = mailing_list.MailingList()
		self.net_mailing_list = {}
		self.cmd_handler = {}
		self.quit = False
		self.stat = None
		self.debug = False
		self.verbose = False
		self.started = False
		self.__input_protocol_version = "0.1.4"
		self.__view_protocol_version = "0.1.4"
		self.__input_buffer = net_buffer.NetBuffer()
		self.__view_buffer = net_buffer.NetBuffer()
		random.seed()

	# Convert a (role,type,arg) to string (to be sent throw network)
	def createMsg(self, role, type, arg=None):
		if arg != None:
			return "%s:%s:%s" % (role, type, arg)
		else:
			return "%s:%s" % (role, type)

	# A newtork client would like to receive all messages of given role
	def registerNetMessage(self, client, role):
		self.mailing_list.registerNet(role, client)

	# A local client would like to receive all messages of given role
	def registerMessage(self, agent, role):
		self.mailing_list.register(role, agent)

	# Create all agents
	def createAgents(self):
		pass
	
	def initIO(self, max_view, view_port, max_input, input_port):
		self.__view_io.name = "view server"
		self.__view_io.on_client_connect = self.openView
		self.__view_io.on_client_disconnect = self.closeView
#		self.__view_io.on_binding_error = self.bindingError
		self.__view_io.on_new_packet = self.recvViewPacket
		self.__view_io.connect('', view_port) #, max_view)

		self.__input_io.name = "input server"
		self.__input_io.on_client_connect = self.openInput
		self.__input_io.on_client_disconnect = self.closeInput
#		self.__input_io.on_binding_error = self.bindingError
		self.__input_io.on_new_packet = self.recvInputPacket
		self.__input_io.connect('', input_port) #, max_input)
	
		thread.start_new_thread( self.run_io_thread, ())
		
	def recvInputPacket(self, packet):
		self.__input_buffer.append(packet.recv_from.addr, packet)
		
	def recvViewPacket(self, packet):
		msg = packet.data
		self.__view_buffer.append(packet.recv_from.addr, packet)
	
	# Function which should be called in a thread
	def run_io_thread(self):
		try:
			while self.__input_io.isRunning() and self.__view_io.isRunning():
				self.__input_io.live()				
				self.__view_io.live()				
				time.sleep(0.001)
		except Exception, msg:
			print "EXCEPTION IN IO THREAD :"
			print msg
			print "--"			
			traceback.print_exc()
			self.stop()
			
	def bindingError(self, server):
		print "Binding error for %s (port %u) !" % (server.name, server.port)
		self.quit = True

	def readViewAnswer(self, client):
		return self.__readClientAnswer(self.__view_buffer, client)
		
	def readInputAnswer(self, client):
		return self.__readClientAnswer(self.__input_buffer, client)
		
	def __readClientAnswer(self, buffer, client, timeout=3.000):
		answer = buffer.readBlocking(client.addr, timeout)
		if answer==None: return None
		answer = answer.data
		return answer
		
	def openView(self, client):
		thread.start_new_thread( self.__clientChallenge, (client,self.__do_openView,"VIEW",))

	def openInput(self, client):
		thread.start_new_thread( self.__clientChallenge, (client,self.__do_openInput,"INPUT",))

	def __clientChallenge(self, client, func, client_type):
		try:
			func(client)
		except Exception, msg:
			print "EXCEPTION WHEN %s TRY TO CONNECT :" % (client_type)
			print msg
			print "--"
			traceback.print_exc()
			self.stop()
	
	def __do_openView(self, client):
		print "View %s try to connect ..." % (client.name)
		
		self.__view_buffer.clear(client.addr)
		
		# Ask protocol version
		msg = self.createMsg("agent_manager", "AskVersion")
		client.send ( io.Packet(msg) )
		answer = self.readViewAnswer(client)
		if answer != self.__view_protocol_version:
			txt = "Sorry, you don't have same protocol version (%s VS %s)" \
				% (answer, self.__view_protocol_version)
			self.sendText(txt)
			client.disconnect()
			return
		
		# ask client name
		msg = self.createMsg("agent_manager", "AskName")
		client.send ( io.Packet(msg) )
		name = self.readViewAnswer(client)
		if name not in ("-", ""): client.name = name

		self.registerNetMessage (client, "agent_manager")
		self.registerNetMessage (client, "game")
		for agent in self.agents:
			msg = self.createMsg("agent_manager", "Create", "%s:%u" % (agent.type, agent.id))
			client.send ( io.Packet(msg) )
			answer = self.readViewAnswer(client)
			if answer == "yes": 
				role = self.readViewAnswer(client)
				while role != ".":
					self.registerNetMessage(client, role)
					role = self.readViewAnswer(client)
				agent.sync(client)

		msg = self.createMsg("game", "Start")
		client.send ( io.Packet(msg) )
			
		txt = "Welcome to new (view) client : %s" % (client.name)
		self.sendText(txt)
		print "View %s connected." % (client.name)

	def __do_openInput(self, client):
		print "Input %s try to connect ..." % (client.name)

		self.__input_buffer.clear(client.addr)

		client.send ( io.Packet("Version?") )
		answer = self.readInputAnswer(client)
		if answer == None:
			if self.verbose: print "Client doesn't sent version"
			client.disconnect()
			return
		if answer != self.__input_protocol_version:
			txt = "Sorry, you don't have same protocol version (%s VS %s)" \
				% (answer, self.__input_protocol_version)
			self.sendText (txt, client)
			client.disconnect()
			return	
		client.send (io.Packet("OK"))
		
		# ask client name
		client.send (io.Packet("Name?"))
		name = self.readInputAnswer(client)
		if name == None:
			if self.verbose: print "Client doesn't sent name"
			client.disconnect()
			return
		if name not in ("-", ""): client.name = name
		client.send (io.Packet("OK"))

		self.__inputs.append (client)
		print "Input %s connected." % (client.name)
		txt = "Welcome to new (input) client : %s" % (client.name)
		self.sendText(txt)

	def closeInput(self, client):
		print "Input %s disconnected." % (client.name)
		if not (client in self.__inputs): return
		self.__inputs.remove (client)
		txt = "Client %s (input) leave us." % (client.name)
		self.sendText(txt)

	def closeView(self, client):
		print "View %s disconnected." % (client.name)
		txt = "Client %s (view) leave us." % (client.name)
		self.sendText(txt)

	def start(self, arg):
		self.stat = ServerStat(self)
		self.initIO(arg["max-view"], arg["view-port"], arg["max-input"], arg["input-port"])
		self.__view_io.on_send = self.stat.onNetSend
		self.__input_io.on_send = self.stat.onNetSend
		self.__view_io.on_receive = self.stat.onNetReceive
		self.__input_io.on_receive = self.stat.onNetReceive

		self.createAgents()

	def setDebug(self, debug):
		self.debug = debug
		self.__view_io.debug = debug
		self.__input_io.debug = debug

	def setVerbose(self, verbose):
		self.verbose = verbose
		self.__view_io.verbose = verbose
		self.__input_io.verbose = verbose

	def connectAgent(self, cmd, agent):
		if self.cmd_handler.has_key(cmd):
			self.cmd_handler[cmd].append (agent)
		else:
			self.cmd_handler[cmd] = [agent]
		
	def registerAgent(self, agent):
		agent.id = 1+len(self.agents)
		agent.server = self
		self.agents.append(agent)
		agent.start()

	def sendMsgToClient(self, client, role, type, arg=None, skippable=False):
		msg = self.createMsg(role, type, arg)
		p = io.Packet(msg)
		p.skippable = skippable
		client.send(p)
		
	def sendText(self, txt, client=None):
		if client != None:
			msg = self.createMsg("agent_manager", "Text", txt)
			client.send( io.Packet(msg) )
		else:
			self.sendMsg("agent_manager", "Text", txt)

	def sendMsg(self, role, type, arg=None, skippable=False):
		msg = AgentMessage(role, type, arg)
		locals = self.mailing_list.getLocal(role)
		for agent in locals:
			agent.putMessage(msg)
		
		msg = self.createMsg(role, type, arg)
		clients = self.mailing_list.getNet(role)
		for client in clients:
			client.send ( io.Packet(msg, skippable = skippable) )
		
	def processCmd(self, cmd):
		if self.debug: print "Received %s." % (cmd)
		if self.cmd_handler.has_key(cmd):
			for agent in self.cmd_handler[cmd]:
				print "Send %s to agent %u." % (cmd, agent.id)
				msg = AgentMessage(agent.id, "Command", cmd)
				agent.putMessage(msg)

	def processInputPacket(self, new_packet):
		self.processInputCmd( new_packet.recv_from, new_packet.data )
	
	def processInputCmd(self, input, cmd):
		pass
		
	def processInputs(self):
		inputs = self.__inputs[:]
		for client in inputs:
			packets = self.__input_buffer.readNonBlocking(client.addr)

			for packet in packets:	
				#if len(cmd)==0: continue
				#if max_len<len(cmd): cmd=cmd[:max_len]
				self.processInputCmd (packet.recv_from, packet.data)

	def live(self):
		if not self.started:
			self.started = True
			print "Server started (waiting for clients ;-))"
			
		self.processInputs()
		for agent in self.agents:
			agent.live()
			if self.quit==True: break

	def stop(self):
		self.__view_io.stop()
		self.__input_io.stop()
		self.agents = {}				
		self.quit = True

	def getNbInput(self): return len(self.__input_io.clients)
	def getNbView(self): return len(self.__view_io.clients)
	def getMaxNbInput(self): return self.__input_io.max_clients
	def getMaxNbView(self): return self.__view_io.max_clients
