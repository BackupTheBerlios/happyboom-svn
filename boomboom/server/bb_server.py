from agents import Character, Projectile, Weapon, World, Game
from base_server import HappyBoomServer, HappyBoomGateway, HappyBoomMessage
from pysma import Kernel

class BoomBoomGateway(HappyBoomGateway):
    def __init__(self, server, arg):
        HappyBoomGateway.__init__(self, server, arg)

    def born(self):
        HappyBoomGateway.born(self)
        self.requestActions("game")
        self.requestActions("weapon")
        self.requestActions("character")
        self.requestActions("world")
        self.requestActions("projectile")

    def start(self):
        if self._verbose: print "[*] Creating agents"
        self.addAgent(Game(debug=self._debug))
        self.addAgent(World(debug=self._debug))
        self.addAgent(Character(100, 1, debug=self._debug))
        self.addAgent(Character(-150, 2, debug=self._debug))
        self.addAgent(Weapon(debug=self._debug))
        self.addAgent(Projectile(debug=self._debug))
        self.sendBroadcastMessage(HappyBoomMessage("start", ()), "game")
                        
    def msg_game_next_character(self, char, team):
        if self._debug: print "Next character : %s,%s" %(char, team)
        self.nextChar = char
                        
    def msg_game_next_turn(self):
        if self._debug: print "Next turn : %s" %self.nextChar
        self.sendNetworkMessage("game", "next_turn")
        self.sendNetworkMessage("game", "active_character", self.nextChar)
        
    def msg_game_collision(self, x, y):
        if self._debug: print "Hit ground : %s,%s" %(x, y)
        self.sendNetworkMessage("projectile", "hit_ground")
    
    def msg_projectile_move(self, x, y):
        if self._debug: print "Projectile move : %s,%s" %(x, y)
        self.sendNetworkMessage("projectile", "move", "%i,%i" %(x,y), True)
        
    def msg_projectile_activate(self, flag):
        if self._debug: print "Projectile activate : %s" %flag
        self.sendNetworkMessage("projectile", "activate", "%u" %(flag))
        
    def msg_weapon_angle(self, a):
        if self._debug: print "Weapon angle : %s" %a
        self.sendNetworkMessage("weapon", "angle", a)
        
    def msg_weapon_strength(self, s):
        if self._debug: print "Weapon strength : %s" %s
        self.sendNetworkMessage("weapon", "force", s)
        
    def msg_world_create(self, m):
        if self._debug: print "World create : %s" %m
        self.sendNetworkMessage("world", "create", m)
        
    def msg_character_move(self, m):
        if self._debug: print "Character move : %s" %m
        self.sendNetworkMessage("character", "move", m)
        
    def msg_new_item(self, type, id):
        if self._debug: print "New item : %s,%s" %(type, id)
        self.__items.append((type, id))
        
    def msg_game_current_character(self, char, team):
        if self._debug: print "Current character : %s,%s" %(char, team)
        self.sendNetworkMessage("game", "active_character", char)

class BoomBoomServer(HappyBoomServer):
    def __init__(self, arg):
        arg["gateway"] = BoomBoomGateway(self, arg)
        HappyBoomServer.__init__(self, arg)
