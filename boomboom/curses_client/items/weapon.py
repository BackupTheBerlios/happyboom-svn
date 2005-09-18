"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from curses_client.item import Item
from curses_client.curses_tools import convertXY
import curses 

class Weapon(Item):
    feature = "weapon"
    
    def __init__(self, id):
        """ Weapon item constructor. """
        Item.__init__(self)
        self.__angle = None 
        self.__strength = None
        self.x, self.y = (None, 10)
        self.character_pos = {}
        self.active_character = None
        self.registerEvent("weapon")
        self.registerEvent("character")

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
        
    def evt_character_activate(self, id):
        """ Active character abcsisse event handler.
        @param event: Event with "active_character_abscisse" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.active_character = id
        self.updateXY()
               
    def draw(self, screen):
        """ Drawing method called by C{BoomBoomDrawer}
        @param screen: Offscreen to draw in.
        @type screen: C{L{Window<bb_drawer.Window>}}
        """
        if self.__angle == None: return
        if self.__strength == None: return
        if self.x == None: return
        maxy,maxx = screen.getmaxyx()
        x, y = convertXY(screen, self.x, self.y)
        if x < maxx/2:
            x = 1
        else:
            x = maxx - 20
        y = 1
        txt = "Angle: %s" % self.__angle
        screen.addstr(y, x, txt)
        txt = "Strength: %s" % self.__strength
        screen.addstr(y+1, x, txt)

    def updateXY(self):
        if self.active_character==None: return
        pos = self.character_pos.get(self.active_character, None)
        if pos == None: return
        self.x, self.y = pos
        
