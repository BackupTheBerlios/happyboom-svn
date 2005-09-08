from bb_agent import BoomBoomAgent, BoomBoomMessage
from agents import Character, Projectile, Weapon, World, Game
from net import io, io_udp, io_tcp, net_buffer
from pysma import Kernel, DummyScheduler
import re, random, thread, traceback, time

class Gateway(BoomBoomAgent):
    def __init__(self):
		BoomBoomAgent.__init__(self, "gateway")
		self.nextChar = None

class BaseServer:
	def __init__(self, maxDisplay=2, displayPort=12430, maxInput=2, inputPort=12431, verbose=False, debug=False):
		self.__protocol_version = "0.1.4"
		self.__debug = debug
		self.__verbose = verbose
		self.__inputs = []
		self.__items = []
		self.__stopped = False
		self.__stoplock = thread.allocate_lock()
		self.__supportedFeatures = {}

        # Create IO
		self.__io = io_tcp.IO_TCP(is_server=True)
		self.__io.debug = debug
		self.__io.verbose = verbose
		self.__io_buffer = net_buffer.NetBuffer()

		self.maxDisplay = maxDisplay
		self.displayPort = displayPort
		self.maxInput = maxInput
		self.inputPort = inputPort
		self.started = False
		random.seed()
		Kernel().addAgent(DummyScheduler(sleep=0.01))
		
	def born(self):
		BoomBoomAgent.born(self)
		self.requestActions("game")
		self.requestActions("weapon")
		self.requestActions("character")
		self.requestActions("world")
		self.requestActions("projectile")
		
	def start(self):
		if self.__verbose: print "[*] Starting server..."
		self.initIO()
		self.createAgents()
		print "[*] Server started"
		
		self.__stoplock.acquire()
		running = not self.__stopped
		self.__stoplock.release()
		while running:
			self.processInputs()
			time.sleep(0.01)
			self.__stoplock.acquire()
			running = not self.__stopped
			self.__stoplock.release()

	def stop(self):
		self.__stoplock.acquire()
		if self.__stopped:
			self.__stoplock.release()
			return
		self.__stopped = True
		self.__stoplock.release()
		print "[*] Stopping server..."
		Kernel.instance.stopKernel()
		self.sendNetworkMessage("game", "Stop", skippable=True)
		self.__display_io.stop()
		self.__input_io.stop()
		if self.__verbose: print "[*] Server stopped"

	def initIO(self):
		if self.__verbose: print "[*] Starting display server"
		self.__display_io.name = "display server"
		self.__display_io.on_client_connect = self.openDisplay
		self.__display_io.on_client_disconnect = self.closeDisplay
		self.__display_io.on_new_packet = self.recvDisplayPacket
		self.__display_io.connect('', self.displayPort)
		if self.__verbose: print "[*] Starting input server"
		self.__input_io.name = "input server"
		self.__input_io.on_client_connect = self.openInput
		self.__input_io.on_client_disconnect = self.closeInput
		self.__input_io.on_new_packet = self.recvInputPacket
		self.__input_io.connect('', self.inputPort)
		thread.start_new_thread(self.run_io_thread, ())
		
	def createAgents(self):
		if self.__verbose: print "[*] Creating agents"
		Kernel.instance.addAgent(self)
		self.addAgent(Game(debug=self.__debug))
		self.addAgent(World(debug=self.__debug))
		self.addAgent(Character(100, 1, debug=self.__debug))
		self.addAgent(Character(-150, 2, debug=self.__debug))
		self.addAgent(Weapon(debug=self.__debug))
		self.addAgent(Projectile(debug=self.__debug))
		self.sendBroadcastMessage(BoomBoomMessage("start", ()), "game")
		
	def openDisplay(self, client):
		thread.start_new_thread( self.__clientChallenge, (client,self.__do_openDisplay,"DISPLAY",))

	def openInput(self, client):
		thread.start_new_thread( self.__clientChallenge, (client,self.__do_openInput,"INPUT",))
		
	def closeInput(self, client):
		if self.__verbose: print "[*] Input %s disconnected." % (client.name)
		if not (client in self.__inputs): return
		self.__inputs.remove (client)
		txt = "Client %s (input) leave us." % (client.name)
		self.sendText(txt)

	def closeDisplay(self, client):
		if self.__verbose: print "[*] Display %s disconnected." % (client.name)
		txt = "Client %s (display) leave us." % (client.name)
		self.sendText(txt)
		
	def __clientChallenge(self, client, func, client_type):
		try:
			func(client)
		except Exception, msg:
			print "EXCEPTION WHEN %s TRY TO CONNECT :" % (client_type)
			print msg
			print "--"
			traceback.print_exc()
			self.stop()

	# Function which should be called in a thread
	def run_io_thread(self):
		try:
			while self.__input_io.isRunning() and self.__display_io.isRunning():
				self.__input_io.live()				
				self.__display_io.live()				
				time.sleep(0.001)
		except Exception, msg:
			print "EXCEPTION IN IO THREAD :"
			print msg
			print "--"			
			traceback.print_exc()
			self.stop()

	def __do_openDisplay(self, client):
		if self.__verbose: print "[*] Display %s try to connect ..." % (client.name)
		
		self.__display_buffer.clear(client.addr)
		
		# Ask protocol version
		msg = self.createMsg("agent_manager", "AskVersion")
		client.send(io.Packet(msg))
		answer = self.readDisplayAnswer(client)
		if answer != self.__display_protocol_version:
			txt = "Sorry, you don't have same protocol version (%s VS %s)" \
				% (answer, self.__display_protocol_version)
			self.sendText(txt)
			client.disconnect()
			return
		
		# ask client name
		msg = self.createMsg("agent_manager", "AskName")
		client.send(io.Packet(msg))
		name = self.readDisplayAnswer(client)
		if name not in ("-", ""): client.name = name

		self.registerFeature(client, "agent_manager")
		self.registerFeature(client, "game")
		for type, id in self.__items:
			msg = self.createMsg("agent_manager", "Create", "%s:%u" % (type, id))
			client.send (io.Packet(msg))
			answer = self.readDisplayAnswer(client)
			if answer == "yes": 
				role = self.readDisplayAnswer(client)
				while role != ".":
					self.registerFeature(client, role)
					role = self.readDisplayAnswer(client)

		msg = self.createMsg("game", "Start")
		client.send(io.Packet(msg))
			
		txt = "Welcome to new (display) client : %s" % (client.name)
		self.sendText(txt)
		if self.__verbose: print "[*] Display %s connected" % (client.name)
		self.sendBBMessage("sync")

	def __do_openInput(self, client):
		if self.__verbose: print "[*] Input %s try to connect ..." % (client.name)

		self.__input_buffer.clear(client.addr)

		client.send(io.Packet("Version?"))
		answer = self.readInputAnswer(client)
		if answer == None:
			if self.__verbose: print "[*] Client doesn't sent version"
			client.disconnect()
			return
		if answer != self.__input_protocol_version:
			txt = "Sorry, you don't have same protocol version (%s VS %s)" \
				% (answer, self.__input_protocol_version)
			self.sendText(txt, client)
			client.disconnect()
			return	
		client.send(io.Packet("OK"))
		
		# ask client name
		client.send(io.Packet("Name?"))
		name = self.readInputAnswer(client)
		if name == None:
			if self.__verbose: print "[*] Client doesn't sent name"
			client.disconnect()
			return
		if name not in ("-", ""): client.name = name
		client.send(io.Packet("OK"))

		self.__inputs.append (client)
		if self.__verbose: print "Input %s connected." % (client.name)
		txt = "Welcome to new (input) client : %s" % (client.name)
		self.sendText(txt)
		
	# Convert a (role,type,arg) to string (to be sent throw network)
	def createMsg(self, role, type, arg=None):
		if arg != None:
			return "%s:%s:%s" % (role, type, arg)
		else:
			return "%s:%s" % (role, type)
		
	def recvInputPacket(self, packet):
		self.__input_buffer.append(packet.recv_from.addr, packet)
		
	def recvDisplayPacket(self, packet):
		msg = packet.data
		self.__display_buffer.append(packet.recv_from.addr, packet)

	def readDisplayAnswer(self, client):
		return self.__readClientAnswer(self.__display_buffer, client)
		
	def readInputAnswer(self, client):
		return self.__readClientAnswer(self.__input_buffer, client)

	def __readClientAnswer(self, buffer, client, timeout=3.000):
		answer = buffer.readBlocking(client.addr, timeout)
		if answer==None: return None
		answer = answer.data
		return answer

	def sendText(self, txt, client=None):
		if client != None:
			msg = self.createMsg("agent_manager", "Text", txt)
			client.send(io.Packet(msg))
		else:
			self.sendNetworkMessage("agent_manager", "Text", txt)

	def processInputCmd(self, input, cmd):
		cmd_ok = (\
			"move_left", "move_right", "move_up", "move_down",
			"shoot", )
		if self.__verbose and cmd != "Ping?":
			print "Command from %s: %s" % (input.name, cmd)
		if re.compile("^chat:(.*)$").match(cmd) != None:
			print "New chat message: %s" % (r.group(1))
			self.sendNetworkMessage("chat_server", "new", r.group(1))
		elif cmd in cmd_ok:	self.sendBroadcastMessage(BoomBoomMessage("new_command", (cmd,)), "command_manager")
		
	def processInputs(self):
		inputs = self.__inputs[:]
		for client in inputs:
			packets = self.__input_buffer.readNonBlocking(client.addr)

			for packet in packets:	
				self.processInputCmd (packet.recv_from, packet.data)

	def registerFeature(self, client, role):
		if role in self.__supportedFeatures:
			if client not in self.__supportedFeatures[role]:
				self.__supportedFeatures[role].append(client)
		else:
			self.__supportedFeatures[role] = [client,]

	def sendNetworkMessage(self, role, type, arg=None, skippable=False):
		msg = self.createMsg(role, type, arg)
		clients = self.__supportedFeatures.get(role, ())
		for client in clients:
			client.send (io.Packet(msg, skippable=skippable))
						
	def msg_game_next_character(self, char, team):
		if self.__debug: print "Next character : %s,%s" %(char, team)
		self.nextChar = char
						
	def msg_game_next_turn(self):
		if self.__debug: print "Next turn : %s" %self.nextChar
		self.sendNetworkMessage("game", "next_turn")
		self.sendNetworkMessage("game", "active_character", self.nextChar)
		
	def msg_game_collision(self, x, y):
		if self.__debug: print "Hit ground : %s,%s" %(x, y)
		self.sendNetworkMessage("projectile", "hit_ground")
	
	def msg_projectile_move(self, x, y):
		if self.__debug: print "Projectile move : %s,%s" %(x, y)
		self.sendNetworkMessage("projectile", "move", "%i,%i" %(x,y), True)
		
	def msg_projectile_activate(self, flag):
		if self.__debug: print "Projectile activate : %s" %flag
		self.sendNetworkMessage("projectile", "activate", "%u" %(flag))
		
	def msg_weapon_angle(self, a):
		if self.__debug: print "Weapon angle : %s" %a
		self.sendNetworkMessage("weapon", "angle", a)
		
	def msg_weapon_strength(self, s):
		if self.__debug: print "Weapon strength : %s" %s
		self.sendNetworkMessage("weapon", "force", s)
		
	def msg_world_create(self, m):
		if self.__debug: print "World create : %s" %m
		self.sendNetworkMessage("world", "create", m)
		
	def msg_character_move(self, m):
		if self.__debug: print "Character move : %s" %m
		self.sendNetworkMessage("character", "move", m)
		
	def msg_new_item(self, type, id):
		if self.__debug: print "New item : %s,%s" %(type, id)
		self.__items.append((type, id))
		
	def msg_game_current_character(self, char, team):
		if self.__debug: print "Current character : %s,%s" %(char, team)
		self.sendNetworkMessage("game", "active_character", char)
