from happyboom.server.base_server import \
    Server as HBServer, \
    Gateway as HBGateway, \
    ClientManager
from pysma import Kernel
from bb_agent import Message
from agents import Character, Projectile, Weapon, World, Game
from happyboom.common.log import log

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
        if self._verbose: log.info("[*] Creating agents")
        self.addAgent(Game(self, debug=self._debug))
        self.addAgent(World(self, debug=self._debug))
        self.addAgent(Character(self, 100, 1, debug=self._debug))
        self.addAgent(Character(self, -150, 2, debug=self._debug))
        self.addAgent(Weapon(self, debug=self._debug))
        self.addAgent(Projectile(self, debug=self._debug))
        self.sendBroadcastMessage(Message("start", ()), "game")
                        
    def msg_game_next_character(self, char, team):
        if self._debug: log.info("Next character : %s,%s" %(char, team))
        self.nextChar = char
                        
    def msg_new_item(self, type, id):
        if self._debug: log.info("New item : %s,%s" %(type, id))
        self.__items.append((type, id))
        
class Server(HBServer):
    def __init__(self, protocol, arg):
        manager = ClientManager(arg)
        gateway = Gateway(protocol, manager, arg)
        HBServer.__init__(self, gateway, arg)
