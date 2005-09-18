"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from client.bb_item import BoomBoomItem
from client.curses_tools import convertXY
import curses

class Projectile(BoomBoomItem):
    """ Represents a banana projectile launch by the monkey.
    @ivar visual: Graphical object containing data and transformations
    @type visual: C{L{VisualObject}}
    """
    
    def __init__(self, args):
        """ Projectile itemp constructor. """
        BoomBoomItem.__init__(self)
        self.registerEvent("projectile")
        self.window = args["window"]
        self.x, self.y = 10,10
        self.display = False

    def draw(self):
        if not self.display: return
        maxy, maxx = self.window.getmaxyx()
        if self.x < 0 or maxx < self.x: return
        if self.y < 0 or maxy < self.y: return
        self.window.addstr(self.y,self.x,"*")
        
    def evt_projectile_move(self, x, y):
        height,width = self.window.getmaxyx()
        self.x, self.y = convertXY(x, y)
        
#    def evt_projectile_hitGround(self, x, y):
#        pass
        
    def evt_projectile_activate(self, state):
        self.display = state
