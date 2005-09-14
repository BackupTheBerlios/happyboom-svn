from happyboom.server.base_server import \
    Server as HBServer, \
    Gateway as HBGateway, \
    ClientManager
from pysma import Kernel
from bb_agent import Message
from agents import Character, Projectile, Weapon, World, Game

class Gateway(HBGateway):
    def __init__(self, protocol, manager, arg):
        HBGateway.__init__(self, protocol, manager, arg)

    def born(self):
        HBGateway.born(self)
        self.requestActions("game")
        self.requestActions("weapon")
        self.requestActions("character")
        self.requestActions("world")
        self.requestActions("projectile")

    def start(self):
        HBGateway.start(self)
        if self._verbose: print "[*] Creating agents"
        self.addAgent(Game(self, debug=self._debug))
        self.addAgent(World(self, debug=self._debug))
        self.addAgent(Character(self, 100, 1, debug=self._debug))
        self.addAgent(Character(self, -150, 2, debug=self._debug))
        self.addAgent(Weapon(self, debug=self._debug))
        self.addAgent(Projectile(self, debug=self._debug))
        self.sendBroadcastMessage(Message("start", ()), "game")
                        
    def msg_game_next_character(self, char, team):
        if self._debug: print "Next character : %s,%s" %(char, team)
        self.nextChar = char
                        
    def msg_game_collision(self, x, y):
        if self._debug: print "Hit ground : %s,%s" %(x, y)
        self.sendNetMsg("projectile", "hit_ground")
    
    def msg_world_create(self, m):
        if self._debug: print "World create : %s" %m
        self.sendNetMsg("world", "create", m)
        
    def msg_character_move(self, m):
        if self._debug: print "Character move : %s" %m
        self.sendNetMsg("character", "move", m)
        
    def msg_new_item(self, type, id):
        if self._debug: print "New item : %s,%s" %(type, id)
        self.__items.append((type, id))
        
    def msg_game_current_character(self, char, team):
        if self._debug: print "Current character : %s,%s" %(char, team)
        self.sendNetMsg("game", "active_character", char)

class Server(HBServer):
    def __init__(self, protocol, arg):
        manager = ClientManager(arg)
        gateway = Gateway(protocol, manager, arg)
        HBServer.__init__(self, gateway, arg)
