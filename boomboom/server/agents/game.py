from server.bb_agent import BoomBoomAgent, BoomBoomMessage
import traceback

class Game(BoomBoomAgent):
    def __init__(self, **args):
        BoomBoomAgent.__init__(self, "game", **args)
        self.teams = []
        self.characters = {}
        self.next_team_pos = None
        self.next_char_pos = {}
        self.current = (None, None)

    def born(self):
        BoomBoomAgent.born(self)
        self.requestActions("world")
        self.requestActions("network")

    def sendNextCharacter(self, char_pos, team_pos):
        if self.next_team_pos != None:
            self.current = (self.nextCharacter, self.nextTeam)
        self.next_team_pos = team_pos
        self.next_char_pos[self.nextTeam] = char_pos
        self.sendBBMessage("next_character", self.nextCharacter, self.nextTeam)

    def msg_network_sync(self):
        self.sync()

    def msg_new_character(self, character, team):
        if team in self.teams:
            self.characters[team].append(character)
        else:
            self.teams.append(team)
            self.characters[team] = [character,]
            self.next_char_pos[team] = 0

    def sync(self):
        char, team = self.current
        self.sendBroadcastMessage(BoomBoomMessage("game_current_character", (char, team)), "network")

    def __getNextCharacter(self):
        return self.characters[self.nextTeam][self.next_char_pos[self.nextTeam]]
    nextCharacter = property(__getNextCharacter)

    def __getNextTeam(self):
        return self.teams[self.next_team_pos]
    nextTeam = property(__getNextTeam)

    def incCharacter(self):
        tpos = (self.next_team_pos + 1) % 2
        cpos = (self.next_char_pos[self.teams[tpos]] + 1) % len(self.characters[self.teams[tpos]])
        self.sendNextCharacter(cpos, tpos)

    def msg_world_collision(self, x, y):
        self.sendBBMessage("next_turn")
        self.incCharacter()
        
    def msg_start(self):
        self.launchGame()

    def launchGame(self):    
        self.sendNextCharacter(0, 0)
        self.sendBBMessage("next_turn")
        self.incCharacter()