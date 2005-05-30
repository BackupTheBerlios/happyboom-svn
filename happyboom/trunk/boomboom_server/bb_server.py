from server import base_server
from server import stat
from bb_agents import *
from world import *
from weapon import *
from character import *
from projectile import *
import re

class BoomBoomServer(base_server.BaseServer):
	def __init__(self):
		base_server.BaseServer.__init__(self)
		self.game_state = None
		self.world = None

	def getActiveCharacter(self):
		if self.game_state == None: return None
		return self.game_state.active_character

	def getActiveTeam(self):
		c = self.getActiveCharacter()
		if c==None: return c
		return c.team

	def createBoomBoomAgents(self):
		self.game_state = GameStateAgent()
		self.registerAgent(self.game_state)

		agent = stat.ServerStatAgent()
		self.registerAgent(agent)

		self.world = World()
		self.registerAgent(self.world)

		agent = CharacterAgent(100, 1)
		agent.findPlace (self.world)
		self.game_state.addCharacter(agent)
		self.registerAgent(agent)

		agent = CharacterAgent(self.world.width-150, 2)
		agent.findPlace (self.world)
		self.game_state.addCharacter(agent)
		self.registerAgent(agent)

		self.registerAgent( Weapon() )

		self.registerAgent( Projectile() )

	def start(self, args):
		base_server.BaseServer.start(self, args)
		self.createBoomBoomAgents()

	def processInputCmd(self, input, cmd):
		cmd_ok = (\
			"move_left", "move_right", "move_up", "move_down",
			"shoot", )
		if self.verbose and cmd != "Ping?":
			print "Command from %s: %s" % (input.name, cmd)
		if re.compile("^chat:(.*)$").match(cmd) != None:
			print "New chat message: %s" % (r.group(1))
			self.sendMsg("chat_server", "new", r.group(1))
		elif cmd in cmd_ok:	self.sendMsg ("command", "new", cmd)
