from server import server_agent

class GameStateAgent(server_agent.ServerAgent):
	def __init__(self):
		server_agent.ServerAgent.__init__(self, "game_state")
		self.msg_handler["command"] = {"new": self.evtCommand}
		self.characters = []
		self.active_character = None
		self.active_pos = None

	def evtCommand(self, cmd):
		if cmd == "move_up": self.move (self.x, self.y - 10)

	def setActiveCharacter(self, pos):
		self.active_character = self.characters[pos]
		if 0<self.active_character.id:
			self.sendMsg("game", "active_character", "%u" % (self.active_character.id))
		self.active_pos = pos

	def sync(self, client):
		self.setActiveCharacter(self.active_pos)

	def addCharacter(self, character):
		self.characters.append(character)
		if self.active_character == None:
			self.setActiveCharacter(0)

	def nextCharacter(self):
		pos = self.active_pos + 1		
		if len(self.characters)<=pos: pos=0
		self.setActiveCharacter(pos)

	def evtCommand(self, cmd):
		if cmd == "next_character": self.nextCharacter()
		
class CharacterAgent(server_agent.ServerAgent):
	def __init__(self):
		server_agent.ServerAgent.__init__(self, "character")
		self.msg_handler["command"] = {"new": self.evtCommand}
		self.x = 10
		self.y = 10

	def evtCommand(self, cmd):
		if self != self.server.game_state.active_character: return
		if cmd == "move_up": self.move (self.x, self.y - 10)
		elif cmd == "move_down": self.move (self.x, self.y + 10)
		elif cmd == "move_left": self.move (self.x-10, self.y)
		elif cmd == "move_right": self.move (self.x+10, self.y)

	def move(self, x, y, force=False):
		if self.x == x and self.y == y and not force: return
		self.x = x
		self.y = y
		self.sendMsg("character", "move", "%u,%i,%i" % (self.id, self.x, self.y))

	def sync(self, client=None):
		self.move(self.x, self.y, force=True)
