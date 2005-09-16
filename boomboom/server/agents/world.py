from server.bb_agent import Agent, Message
import random

class Building:
    def __init__(self, x, y, height, width):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def isPartOf(self, x, y):
        if x < self.x:
            return False
        if self.x + self.width < x:
            return False
        if y < self.y:
            return False
        if self.y + self.height < y:
            return False
        return True


class World(Agent):
    def __init__(self, gateway, **args):
        Agent.__init__(self, "world", gateway, **args)
        self.buildings = None
        self.height = 350
        self.width = 640
        self.registerEvent("gateway")
        self.generate()

    def born(self):
        Agent.born(self)
        self.requestActions("projectile")
        self.requestActions("game")
        self.sendBroadcastMessage(Message("new_item", (self.type, self.id)), "network")

    def generate(self):
        width = self.width
        x = 0
        self.buildings = []
        building_hmin = 100
        building_hmax = self.height-100
        building_wmin = 40
        building_wmax = 60
        while building_wmin<width:
            w = random.randint(building_wmin, building_wmax)
            h = random.randint(building_hmin, building_hmax)
            building = Building(x, self.height-h, h, w)
            self.buildings.append(building)
            width = width - w
            x = x + w
        if 0 < width:
            h = random.randint(building_hmin, building_hmax)
            building = Building(x, self.height-h, h, width)
            self.buildings.append(building)

    def hitGround(self, x, y):
        # Testing screen bounds
        if self.height <= y or x < 0 or self.width <= x:
            return True
        # Testing building collision
        for b in self.buildings:
            if b.isPartOf(x,y):
                return True
        return False    

    def sync(self, client):
        msg = ""
        for b in self.buildings:
            if len(msg) != 0: msg = msg + ";"
            msg = msg + "%i,%i,%i,%i" % (b.x, b.y, b.width, b.height)
        self.sendBroadcastMessage(Message("world_create", (msg,)), "network")
        self.netCreateItem(client)
        self.sendNetMsg("world", "create", msg)

    def msg_character_search_place(self, x0, width, height):
        if x0 < 0:
            x0 = self.width + x0
        else:
            x0 = x0
        x1 = x0 + width
        x = -1
        y = -1
        for b in self.buildings:
            if x1 <= b.x + b.width and width < b.width:
                x = int(b.x + (b.width - width) / 2)
                y = b.y - height
                break
        self.sendMessage(Message("found_place", (x, y)), self.currentMessage.sender)
                
    def msg_projectile_move(self, x, y):
        if self.hitGround(x, y):
            self.send("hitGround", x, y)
            self.sendNetMsg("projectile", "hitGround", int(x), int(y))

    def evt_gateway_syncClient(self, client):
        self.sync(client)
