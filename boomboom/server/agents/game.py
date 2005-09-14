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
        if self.current == None: self.current = 0 

    def sync(self):
        self.sendBroadcast(Message("game_current_character", self.current), "network")

    def incCharacter(self):
        tpos = (self.next_team_pos + 1) % 2
        cpos = (self.next_char_pos[self.teams[tpos]] + 1) % len(self.characters[self.teams[tpos]])
        self.sendNextCharacter(cpos, tpos)

    def nextTurn(self):
        self.send("next_turn")
        self.sendNetMsg("game", "next_turn")
        self.sendNetMsg("game", "active_character", \
            "int", self.current)

    def msg_world_collision(self, x, y):
        self.nextTurn()
        self.incCharacter()
        
    def msg_start(self):
        self.launchGame()

    def launchGame(self):    
        self.sendNextCharacter(0, 0)
        self.nextTurn()
        self.incCharacter()
