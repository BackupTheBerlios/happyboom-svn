from server.bb_agent import Agent, Message
import traceback

class Game(Agent):
    def __init__(self, gateway, **args):
        Agent.__init__(self, "game", gateway, **args)
        self.characters = []
        self.current = None 

    def born(self):
        Agent.born(self)
        self.requestActions("world")
        self.requestActions("network")

    def msg_network_sync(self):
        self.sync()

    def msg_new_character(self, character):
        self.characters.append(character)
        if self.current == None:
            self.setCurrent(0)

    def sync(self):
        self.sendBroadcast(Message("game_current_character", self.current), "network")

    def setCurrent(self, current):
        self.current = current
        self.sendNetMsg("game", "setActiveCharacter", current)

    def nextCharacter(self):
        new = (self.current + 1) % len(self.characters)
        self.setCurrent(new)

    def nextTurn(self):
        self.send("next_turn")
        self.sendNetMsg("game", "nextTurn")
        self.sendNetMsg("game", "setActiveCharacter", self.current)

    def msg_world_collision(self, x, y):
        self.nextTurn()
        self.nextCharacter()
        
    def msg_start(self):
        self.launchGame()

    def launchGame(self):    
        self.setCurrent(self.current)
        self.nextTurn()
