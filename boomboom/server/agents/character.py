from server.bb_agent import BoomBoomAgent, BoomBoomMessage

class Character(BoomBoomAgent):
    def __init__(self, x, team, **args):
        BoomBoomAgent.__init__(self, "character", **args)
        self.x = x
        self.y = 0
        self.width = 28
        self.height = 29
        self.team = team
        self.next = False
        self.current = False
        
    def born(self):
        BoomBoomAgent.born(self)
        self.requestActions("game")
        self.requestActions("network")
        self.sendBroadcastMessage(BoomBoomMessage("character_search_place", (self.x, self.width, self.height)), "world")
        self.sendBroadcastMessage(BoomBoomMessage("new_character", (self.id, self.team)), "game")
        self.sendBroadcastMessage(BoomBoomMessage("new_item", (self.type, self.id)), "network")

    def move(self, x, y, force=False):
        if self.x == x and self.y == y and not force: return
        self.x = x
        self.y = y
        self.sendBroadcastMessage(BoomBoomMessage("character_move", ("%u,%i,%i" % (self.id, self.x, self.y),)), "network")
        if self.current:
            self.sendBBMessage("active_coord", self.x, self.y)

    def sync(self):
        self.move(self.x, self.y, force=True)

    def msg_found_place(self, x, y):
        self.move(x, y, True)
        
    def msg_game_next_character(self, char, team):
        if self.id == char:
            self.next = True
        
    def msg_game_next_turn(self):
        self.current = self.next
        if self.current:
            self.sendBBMessage("active_coord", self.x, self.y)
        self.next = False
        
    def msg_network_sync(self):
        self.sync()