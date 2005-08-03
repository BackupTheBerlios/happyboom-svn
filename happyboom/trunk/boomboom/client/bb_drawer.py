"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from common import simple_event
from common.simple_event import EventListener
import bb_events
import pygame, time

class BoomBoomDrawer(EventListener):
    """ Manages the drawing of the screen game (double buffered) in a display loop.
    @ivar __screen: Current drawed offscreen.
    @type __screen: C{{Window}}
    @ivar __frameTime: Minimum time to draw a frame.
    @type __frameTime: C{float}
    @ivar __items: Objects which have graphical content to draw (visual items) genered by visible item events.
    @type __items: C{list<L{BoomBoomItem}>}
    """
    
    def __init__(self, max_fps=25):
        """ BoomBoomDrawer constructor.
        @param max_fps: Maximal number of frames per second, for optimization.
        @type max_fps: C{int}
        """
        EventListener.__init__(self, prefix="evt_")
        # Current offscreen
        self.__screen = None
        self.__frameTime = 1.0 / max_fps
        self.__items = []
        self.registerEvent(bb_events.visibleItem)
    
    def start(self):
        """ Creates game window and starts display loop. """
        self.__screen = Window(640, 350)
        self.__screen.background_color = (0, 0, 168)
        
        while True:
            live_begin = time.time()
            
            # Clearing screen
            self.__screen.surface.fill(self.__screen.background_color)
            # Drawing each items
            for item in self.__items:
                item.draw(self.__screen)
            # Displaying offscreen 
            pygame.display.flip()
            
            delay = time.time() - live_begin
            if delay < self.__frameTime:
                delay = self.__frameTime - delay
                time.sleep(delay)
        
    def evt_graphical_item(self, event):
        """ active item event handler.
        @param event: Event with "graphical_item" type.
        @type event: C{L{common.simple_event.Event}}
        """
        if event.source not in self.__items:
            self.__items.append(event.source)
        
        
class Window:
    """ Represents a GUI window or surface using pygame.
    @ivar type: Type of pygame surface : "window" or "surface" (panel into another window).
    @type type: C{str}
    @ivar surface: pygame surface object.
    @type surface: C{pygame.Surface}
    """
    def __init__(self, width, height, type="window"):
        """ Window constructor.
        @param width: Width of the window.
        @type width: C{int}
        @param height: Height of the window.
        @type height: C{int}
        @param type: Type of pygame surface : "window" (by default) or "surface".
        @type type: C{str}
        """
        if type=="surface":
            self.type = "surface" 
            self.surface = pygame.Surface((width,height))
        else:
            self.type = "window"
            self.surface = pygame.display.set_mode((width,height))
        self.pos = (0,0)
        self.view_pos = (0,0)
        self.scale = 1
        self.border_color = (255, 255, 255)
        self.background_color = (0, 0, 0)

    def blit(self, surface, pos):
        new_pos = (pos[0] - self.view_pos[0], pos[1] - self.view_pos[1],)
        self.surface.blit(surface, new_pos)