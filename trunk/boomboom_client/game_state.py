from view import *

class GameStateAgent(ViewAgent):
	def __init__(self):
		ViewAgent.__init__(self)
		self.__active_character = None
		self.msg_handler["game"] = {"active_character": self.setActiveCharacter}

	def getActiveCharacter(self):
		if self.__active_character==None: return None
		return self.server.agents.get(self.__active_character, None)
	active_character = property(getActiveCharacter)
		
	def setActiveCharacter(self, arg):
		self.__active_character = int(arg)

	def start(self):
		ViewAgent.start(self)
		self.server.game_state = self
