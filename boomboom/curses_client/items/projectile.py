"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from curses_client.item import Item
from curses_client.curses_tools import convertXY
import curses

class Projectile(Item):
    """ Represents a banana projectile launch by the monkey.
    @ivar visual: Graphical object containing data and transformations
    @type visual: C{L{VisualObject}}
    """
    feature = "projectile"
    
    def __init__(self, id):
        """ Projectile itemp constructor. """
        Item.__init__(self)
        self.registerEvent("projectile")
        self.x, self.y = 10,10
        self.display = False

    def draw(self, screen):
        if not self.display: return
        maxy, maxx = screen.getmaxyx()
        x, y = convertXY(screen, int(self.x), int(self.y))
        if x < 0 or maxx < x: return
        if y < 0 or maxy < y: return
        screen.addstr(y,x,")"+" "*maxx, curses.color_pair(curses.COLOR_YELLOW))
        
    def evt_projectile_move(self, x, y):
        self.x, self.y = (x, y)
        
#    def evt_projectile_hitGround(self, x, y):
#        pass
        
    def evt_projectile_activate(self, state):
        self.display = state
