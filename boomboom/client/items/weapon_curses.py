"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from client.bb_item import BoomBoomItem
import curses 
from client.curses_tools import convertXY

class Weapon(BoomBoomItem):
    def __init__(self, args):
        """ Weapon item constructor. """
        BoomBoomItem.__init__(self)
        self.__angle = None 
        self.__strength = None
        self.x, self.y = (None, 10)
        self.character_pos = {}
        self.window = args["window"]
        self.active_character = None
        self.registerEvent("weapon")
        self.registerEvent("character")
        self.registerEvent("game")

    def evt_weapon_setStrength(self, strength):
        """ Weapon strength event handler.
        @param event: Event with "weapon_force" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.__strength = strength
        
    def evt_weapon_setAngle(self, angle):
        """ Weapon angle event handler.
        @param event: Event with "weapon_angle" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.__angle = angle 

    def evt_character_move(self, id, x, y):
        self.character_pos[id] = (x, y,)
        self.updateXY()
        
    def evt_game_setActiveCharacter(self, id):
        """ Active character abcsisse event handler.
        @param event: Event with "active_character_abscisse" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.active_character = id
        self.updateXY()
               
    def draw(self):
        """ Drawing method called by C{BoomBoomDrawer}
        @param screen: Offscreen to draw in.
        @type screen: C{L{Window<bb_drawer.Window>}}
        """
        if self.__angle == None: return
        if self.__strength == None: return
        if self.x == None: return
        txt = "Angle: %s" % self.__angle
        self.window.addstr(self.y, self.x, txt)
        txt = "Strength: %s" % self.__strength
        self.window.addstr(self.y+1, self.x, txt)

    def updateXY(self):
        if self.active_character==None: return
        pos = self.character_pos.get(self.active_character, None)
        if pos == None: return
        x, y = convertXY(pos[0], pos[1])
        maxy,maxx = self.window.getmaxyx()
        if x < maxx/2:
            self.x = 1
        else:
            self.x = maxx - 20
        self.y = 1
