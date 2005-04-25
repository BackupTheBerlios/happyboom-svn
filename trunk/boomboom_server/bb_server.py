from server import base_server
from bb_agents import *
import re

class BoomBoomServer(base_server.BaseServer):
	def __init__(self):
		base_server.BaseServer.__init__(self)
		self.game_state = None

	def createBoomBoomAgents(self):
		self.game_state = GameStateAgent()
		self.registerAgent(self.game_state)

		agent = CharacterAgent()
		self.game_state.addCharacter(agent)
		self.registerAgent(agent)

		agent = CharacterAgent()
		agent.x = 300
		self.game_state.addCharacter(agent)
		self.registerAgent(agent)

	def start(self, args):
		base_server.BaseServer.start(self, args)
		self.createBoomBoomAgents()

	def processInputCmd(self, input, cmd):
		cmd_ok = ("move_left", "move_right", "move_up", "move_down","next_character",)
		if self.verbose and cmd != "Ping?":
			print "Command from %s: %s" % (input.name, cmd)
		if re.compile("^chat:(.*)$").match(cmd) != None:
			print "New chat message: %s" % (r.group(1))
			self.sendMsg("chat_server", "new", r.group(1))
		elif cmd == "Ping?": input.send("Pong!\n")
		elif cmd in cmd_ok:	self.sendMsg ("command", "new", cmd)
