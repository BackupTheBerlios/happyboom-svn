"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from client import bb_events
from client.bb_item import BoomBoomItem, VisualObject
import os.path
import pygame

class Sun(BoomBoomItem):
    """ Represents a smiling sun which makes "oh" when collided.
    @ivar visual: Graphical object containing data and transformations
    @type visual: C{L{VisualObject}}
    @ivar __visual1: Visual with the smiling sun image.
    @type __visual1: C{L{VisualObject}}
    @ivar __visual2: Visual with the "oh"-ing sun image.
    @type __visual2: C{L{VisualObject}}
    """
    def __init__(self):
        """ Sun item constructor. """
        BoomBoomItem.__init__(self)
        self.__visual1 = VisualObject(os.path.join("data", "sun.png"))
        self.__visual2 = VisualObject(os.path.join("data", "sun2.png"))
        self.__visual1.move (300,10)
        self.__visual2.move (300,10)
        self.visual = self.__visual1
        self.registerEvent(bb_events.nextTurn)
        self.registerEvent(bb_events.projectileMove)
        
    def evt_game_next_turn(self, event):
        """ Next turn event handler.
        @param event: Event with "game_next_turn" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.resetHit()
        
    def evt_projectile_move(self, event):
        """ Projectile move event handler.
        @param event: Event with "projectile_move" type.
        @type event: C{L{common.simple_event.Event}}
        """
        if self.visual == self.__visual2: return
        arg = event.content.split(",")
        x = int(arg[0])
        y = int(arg[1])
        projectile_rect = pygame.Rect([x,y,10,10]) # TODO: Incorrect projectile size!
        if self.visual.rect.colliderect(projectile_rect):
            self.hit()
    
    def resetHit(self):
        """ Shows back the smiling sun. """
        self.visual = self.__visual1
    
    def hit(self):
        """ Shows the sun which makes "oh". """
        self.visual = self.__visual2