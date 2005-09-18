from server.bb_agent import Agent, Message
import traceback

class Game(Agent):
    def __init__(self, gateway, **args):
        Agent.__init__(self, "game", gateway, **args)
        self.characters = []
        self.current = None 
        self.registerEvent("gateway")

    def born(self):
        Agent.born(self)
        self.requestActions("world")
        self.requestActions("network")

    def msg_new_character(self, character):
        self.characters.append(character)
        if self.current == None:
            self.setCurrent(0)

    def setCurrent(self, current):
        self.current = current
        char = self.characters[self.current].id
        self.send("setActiveCharacter", char)
        self.sendNetMsg("character", "activate", char)

    def nextCharacter(self):
        new = (self.current + 1) % len(self.characters)
        self.setCurrent(new)

    def nextTurn(self):
        self.send("next_turn")
        self.sendNetMsg("game", "nextTurn")
        self.setCurrent(self.current)

    def msg_world_hitGround(self, x, y):
        self.nextTurn()
        self.nextCharacter()
        
    def msg_start(self):
        self.launchGame()

    def launchGame(self):    
        self.setCurrent(self.current)
        self.nextTurn()

    def evt_gateway_syncClient(self, client):
        self.sendNetMsg("game", "start")
        self.setCurrent(self.current)
