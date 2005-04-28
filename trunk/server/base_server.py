from net import net_server
from server_agent import *
from stat import *
from common import mailing_list
import string
import time
import thread
import random

class BaseServer(object):
	instance = None
	
	def __init__(self):
		BaseServer.instance = self
		self.agents = []
		self.__view_io = net_server.NetworkServer()
		self.__input_io = net_server.NetworkServer()
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
		self.client_answer = {}
		random.seed()

	# Private are not private ??? :-P
	def getInputIO(self):
		return self.__input_io
	def getViewIO(self):
		return self.__view_io

	def disconnect_client_timeout(self, client, timeout):
		msg = self.createMsg("game", "Stop")
		client.send (msg)
		t = time.time()
		while client.connected:
			time.sleep(0.100)
			# Hack to check if client is still connected
			client.readNonBlocking()
			if timeout < time.time() - t: break
		if not client.connected: return
		print "Timeout (%.1f sec) over!" % (timeout)
		client.disconnect()
	
	# Convert a (role,type,arg) to string (to be sent throw network)
	def createMsg(self, role, type, arg=None):
		if arg != None:
			return "%s:%s:%s\n" % (role, type, arg)
		else:
			return "%s:%s\n" % (role, type)

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
		self.__view_io.on_binding_error = self.bindingError
		self.__view_io.start(view_port, max_view)

		self.__input_io.name = "input server"
		self.__input_io.on_client_connect = self.openInput
		self.__input_io.on_client_disconnect = self.closeInput
		self.__input_io.on_binding_error = self.bindingError
		self.__input_io.start(input_port, max_input)

	def bindingError(self, server):
		print "Binding error for %s (port %u) !" % (server.name, server.port)
		self.quit = True

	def readClientAnswer(self, client, max_len=512):
		if client in self.client_answer:
			answer = self.client_answer[client][0]
			del self.client_answer[client][0]
			if len(self.client_answer[client])==0:
				del self.client_answer[client]
		else:
			answer = client.read()
			if answer == None: return None
			lines = answer.split("\n")
			del lines[-1] # Last line is always empty
			if len(lines)==0:
				if self.debug: print "Wrong client answer : %s" % (answer)
				return None
			if 1<len(lines):
				self.client_answer[client] = lines[1:]
			answer = lines[0]
		if max_len < len(answer): answer = answer[:max_len]
		return answer
		
	def openView(self, client):
		print "View %s try to connect ..." % (client.name)
		
		# Ask protocol version
		client.send ( self.createMsg("agent_manager", "AskVersion") )
		answer = self.readClientAnswer(client, 16)
		if answer != self.__view_protocol_version:
			txt = "Sorry, you don't have same protocol version (%s VS %s)" \
				% (answer, self.__view_protocol_version)
			self.sendText(txt)
			thread.start_new_thread( self.disconnect_client_timeout, (client, 5.0,))
			return
		
		# ask client name
		client.send ( self.createMsg("agent_manager", "AskName") )
		name = self.readClientAnswer(client, 16)
		if name not in ("-", ""): client.name = name

		self.registerNetMessage (client, "agent_manager")
		self.registerNetMessage (client, "game")
		for agent in self.agents:
			msg = self.createMsg("agent_manager", "Create", "%s:%u" % (agent.type, agent.id))
			client.send (msg)
			answer = self.readClientAnswer(client, 3)
			if answer == "yes": 
				role = self.readClientAnswer(client, 50)
				while role != ".":
					self.registerNetMessage(client, role)
					role = self.readClientAnswer(client, 50)
				agent.sync(client)
		client.send ( self.createMsg("game", "Start") )
			
		txt = "Welcome to new (view) client : %s" % (client.name)
		self.sendText(txt)
		print "View %s connected." % (client.name)

	def openInput(self, client):
		print "Input %s try to connect ..." % (client.name)

		client.send ("Version?\n")
		answer = self.readClientAnswer(client, 16)
		if answer == None:
			if self.verbose: print "Client doesn't sent version"
			client.disconnect()
			return
		if answer != self.__input_protocol_version:
			txt = "Sorry, you don't have same protocol version (%s VS %s)" \
				% (answer, self.__input_protocol_version)
			self.sendText (txt, client)
			thread.start_new_thread( self.disconnect_client_timeout, (client, 5.0,))
			return	
		client.send ("OK\n")
		
		# ask client name
		client.send ("Name?\n")
		name = self.readClientAnswer(client, 16)
		if name == None:
			if self.verbose: print "Client doesn't sent name"
			client.disconnect()
			return
		if name not in ("-", ""): client.name = name
		client.send ("OK\n")

		self.__inputs.append (client)
		print "Input %s connected." % (client.name)
		txt = "Welcome to new (input) client : %s" % (client.name)
		self.sendText(txt)

	def closeInput(self, client):
		self.__inputs.remove (client)
		print "Input %s disconnected." % (client.name)
		txt = "Client %s (input) leave us." % (client.name)
		self.sendText(txt)

	def closeView(self, client):
		print "View %s disconnected." % (client.name)
		txt = "Client %s (view) leave us." % (client.name)
		self.sendText(txt)

	def start(self, arg):
		self.stat = ServerStat(self)
		self.initIO(arg["max-view"], arg["view-port"], arg["max-input"], arg["input-port"])
		self.stat.start()
		self.createAgents()

	def setDebug(self, debug):
		self.debug = debug
		self.__view_io.debug = debug
		self.__input_io.debug = debug

	def setVerbose(self, verbose):
		self.verbose = verbose

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

	def sendMsgToClient(self, client, role, type, arg=None):
		msg = self.createMsg(role, type, arg)
		client.send(msg)
		
	def sendText(self, txt, client=None):
		if client != None:
			msg = self.createMsg("agent_manager", "Text", txt)
			client.send(msg)
		else:
			self.sendMsg("agent_manager", "Text", txt)

	def sendMsg(self, role, type, arg=None):
		msg = AgentMessage(role, type, arg)
		locals = self.mailing_list.getLocal(role)
		for agent in locals:
			agent.putMessage(msg)
		
		msg = self.createMsg(role, type, arg)
		clients = self.mailing_list.getNet(role)
		for client in clients: client.send(msg)
		
	def processCmd(self, cmd):
		print "Received %s." % (cmd)
		if self.cmd_handler.has_key(cmd):
			for agent in self.cmd_handler[cmd]:
				print "Send %s to agent %u." % (cmd, agent.id)
				msg = AgentMessage(agent.id, "Command", cmd)
				agent.putMessage(msg)

	def processInputCmd(self, input, cmd):
		pass
		
	def processInputs(self):
		for input in self.__inputs:
			data = input.readNonBlocking()
			if data != None:
				cmds = data.split("\n")
				max_len = 80 
				for cmd in cmds:	
					import re
					if len(cmd)==0: continue
					if max_len<len(cmd): cmd=cmd[:max_len]
					self.processInputCmd (input, cmd)

	def live(self):
		self.__input_io.live()
		self.__view_io.live()
		if not self.__input_io.listening:
			time.sleep (0.250)
			if self.verbose: print "Wait input server initialisation ..."
			return
		if not self.started:
			self.started = True
			print "Server started (waiting for clients ;-))"
		if not self.__input_io.isRunning():
			print "Input server stopped."
			self.stop()
			return
		if not self.__view_io.isRunning():
			print "View server stopped."
			self.stop()
			return			
		if not self.__view_io.listening:
			time.sleep (0.250)
			if self.verbose: print "Wait view server initialisation ..."
			return
			
		self.processInputs()
		for agent in self.agents:
			agent.live()
			if self.quit==True: break

	def stop(self):
		self.sendMsg("game", "Stop")
		self.agents = {}				
		self.quit = True
