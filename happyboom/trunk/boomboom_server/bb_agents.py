from server import server_agent

class GameStateAgent(server_agent.ServerAgent):
	def __init__(self):
		server_agent.ServerAgent.__init__(self, "game_state")
		self.msg_handler["game"] = {\
			"next_turn": self.evtNextTurn}
		self.msg_handler["command"] = {\
			"new": self.evtCommand}
		self.characters = []
		self.__active_character = None
		self.__active_pos = None

	def getActiveCharacter(self):
		return self.__active_character
	active_character = property(getActiveCharacter)

	def setActiveCharacter(self, pos):
		self.__active_character = self.characters[pos]
		if 0<self.__active_character.id:
			self.sendMsg("game", "active_character", "%u" % (self.__active_character.id))
		self.__active_pos = pos

	def sync(self, client):
		self.setActiveCharacter(self.__active_pos)

	def addCharacter(self, character):
		self.characters.append(character)
		if self.__active_character == None:
			self.setActiveCharacter(0)

	def nextCharacter(self):
		pos = self.__active_pos + 1		
		if len(self.characters)<=pos: pos=0
		self.setActiveCharacter(pos)

	def evtNextTurn(self, cmd):
		self.nextCharacter()

	def evtCommand(self, cmd):
		#if cmd == "next_character": self.nextCharacter()
		pass
