"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from client import bb_events
from client.bb_item import BoomBoomItem, VisualObject
import os.path

class Projectile(BoomBoomItem):
    """ Represents a banana projectile launch by the monkey.
    @ivar visual: Graphical object containing data and transformations
    @type visual: C{L{VisualObject}}
    """
    
    def __init__(self):
        """ Projectile itemp constructor. """
        BoomBoomItem.__init__(self)
        
        self.visual = VisualObject(os.path.join("data", "banana.png"))
        self.registerEvent(bb_events.projectileMove)
        self.registerEvent(bb_events.projectileHitGround)
        self.registerEvent(bb_events.projectileActivate)
        
    def evt_projectile_move(self, event):
        """ Projectile move event handler.
        @param event: Event with "projectile_move" type.
        @type event: C{L{common.simple_event.Event}}
        """
        x, y = event.content.split(",")
        self.visual.move(int(x), int(y))
        
    def evt_projectile_hit_ground(self, event):
        """ Projectile hit ground event handler.
        @param event: Event with "projectile_hit_ground" type.
        @type event: C{L{common.simple_event.Event}}
        """
        print "[DISPLAY] Hit ground"
        # TODO: Graphic effect
        
    def evt_projectile_activate(self, event):
        """ Projectile activate event handler.
        @param event: Event with "projectile_activate" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.visual.setVisibility(event.content == '1')