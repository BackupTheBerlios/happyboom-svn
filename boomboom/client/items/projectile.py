"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
#from client import bb_events
from client.item import Item, VisualObject
import os.path

class Projectile(Item):
    """ Represents a banana projectile launch by the monkey.
    @ivar visual: Graphical object containing data and transformations
    @type visual: C{L{VisualObject}}
    """
    
    feature = "projectile"
    
    def __init__(self, id):
        """ Projectile itemp constructor. """
        Item.__init__(self, id)
        self.visual = VisualObject(os.path.join("data", "banana.png"))
        self.registerEvent("projectile")
        
    def evt_projectile_move(self, x, y):
        """ Projectile move event handler.
        @param event: Event with "projectile_move" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.visual.move(x, y)
        
    def evt_projectile_hitGround(self, x, y):
        """ Projectile hit ground event handler.
        @param event: Event with "projectile_hit_ground" type.
        @type event: C{L{common.simple_event.Event}}
        """
        print "[DISPLAY] Hit ground"
        # TODO: Graphic effect
        
    def evt_projectile_activate(self, state):
        """ Projectile activate event handler.
        @param event: Event with "projectile_activate" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.visual.setVisibility(state == 1)
