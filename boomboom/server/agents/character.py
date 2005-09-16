from server.bb_agent import Agent, Message

class Character(Agent):
    def __init__(self, gateway, x, team, **args):
        Agent.__init__(self, "character", gateway, **args)
        self.x = x
        self.y = 0
        self.width = 28
        self.height = 29
        self.team = team
        self.next = False
        self.current = False
        self.registerEvent("gateway")
        
    def born(self):
        Agent.born(self)
        self.requestActions("game")
        self.requestActions("network")
        self.sendBroadcast(Message("character_search_place", (self.x, self.width, self.height)), "world")
        self.sendBroadcast(Message("new_character", (self,)), "game")
        self.sendBroadcast(Message("new_item", (self.type, self.id)), "network")

    def move(self, x, y, force=False):
        if self.x == x and self.y == y and not force: return
        self.x = x
        self.y = y
        self.send("move", self.id, self.x, self.y)
        self.sendNetMsg("character", "move", self.id, self.x, self.y)

    def evt_gateway_syncClientCreate(self, client):
        self.netCreateItem(client)

    def evt_gateway_syncClient(self, client):
        self.move(self.x, self.y, force=True)

    def msg_found_place(self, x, y):
        self.move(x, y, True)
        
    def msg_game_next_turn(self):
        self.current = self.next
        if self.current:
            self.send("active_coord", self.x, self.y)
        self.next = False
