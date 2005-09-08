"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from common import simple_event
from common.simple_event import EventListener, EventLauncher
import bb_events
import pygame

class BoomBoomItem(EventListener, EventLauncher):
    """ Generic class for representing graphical items.
    @ivar visual: Graphical object containing data and transformations
    @type visual: C{L{VisualObject}}
    """
    
    def __init__(self):
        """ BoomBoomItem constructor. """
        EventListener.__init__(self, "evt_")
        EventLauncher.__init__(self)
        self.visual = None
        self.launchEvent(bb_events.visibleItem)
        
    def draw(self, screen):
        """ Drawing method called by C{BoomBoomDrawer}
        @param screen: Offscreen to draw in.
        @type screen: C{L{Window<bb_drawer.Window>}}
        """
        if self.visual == None: return
        self.visual.draw(screen)
        

class VisualObject(object):
    """ Manage representation and transformation of an external image to be drawn into game screen.
    @ivar visible: Visibility item flag (Default: C{True}).
    @type visible: C{bool}
    @ivar surface: Pygame item surface object.
    @type surface: C{pygame.Surface}
    @type rect: C{pygame.Rect}
    @type x: C{int}
    @type y: C{int}
    @type width: C{int}
    @type height: C{int}
    @ivar __x: Item top-left abcsisse.
    @type __x: C{int}
    @ivar __y: Item top-left ordonnee.
    @type __y: C{int}
    @ivar __width: Item width.
    @type __width: C{int}
    @ivar __height: Item height.
    @type __height. C{int}
    @ivar __rect: Including box of the item for collide detection.
    @type __rect: C{pygame.Rect}
    """
    def __init__(self, file):
        """ VisualObject constructor.
        @param file: Path of the external image.
        @type file: C{str}
        """
        self.__x, self.__y = (0,0)
        self.loadImage(file)
        self.visible = True

    def loadImage(self, file):
        """ Loads external image with pygame.
        @param file: Path of the external image.
        @type file: C{str}
        """
        self.surface = pygame.image.load(file).convert_alpha()
        self.__width = self.surface.get_width()
        self.__height = self.surface.get_height()
        self.__rect = pygame.Rect( [self.__x, self.__y, self.__width, self.__height] )

    def move(self, x, y):
        """ Moves the items in absolute coordinates.
        @param x: New abcsisse.
        @type x: C{int}
        @param y: New ordonnee.
        @type y: C{int}
        """
        self.__x = x
        self.__y = y
        self.__rect = pygame.Rect( [self.__x, self.__y, self.__width, self.__height] )

    def __getRect(self):
        """ C{L{rect}} property getter.
        @return: The including box of the item.
        @rtype: C{pygame.Rect}
        """
        return self.__rect
    rect = property(__getRect, doc="Including box of the item for collide detection (read only).")
    
    def __getHeight(self):
        """ C{L{height}} property getter.
        @return: The height of the item.
        @rtype: C{int}
        """
        return self.__height
    height = property(__getHeight, doc="Item height (read only).")
    
    def __getWidth(self):
        """ C{L{width}} property getter.
        @return: The width of the item.
        @rtype: C{int}
        """
        return self.__width
    width = property(__getWidth, doc="Item width (read only).")
    
    def __getX(self):
        """ C{L{x}} property getter.
        @return: The left abcsisse ot the item.
        @rtype: C{int}
        """
        return self.__x
    def __setX(self, x):
        """ C{L{x}} property setter.
        @param x: New item abcsisse.
        @type x: C{int}
        """
        self.move(x, self.__y)
    x = property(__getX, __setX, doc="Item top-left abcsisse.")
    
    def __getY(self):
        """ C{L{y}} property getter.
        @return: The top ordonnee ot the item.
        @rtype: C{int}
        """
        return self.__y
    def __setY(self, y):
        """ C{L{y}} property setter.
        @param y: New item ordonnee.
        @type y: C{int}
        """
        self.move(self.__x, y)
    y = property(__getY, __setY, doc="Item top-left ordonnee.")

    def setVisibility(self, visible):
        """ Sets the visibility of the item.
        @param visible: New visible flag value.
        @type visible: C{bool}
        """
        self.visible = visible
        
    def draw(self, screen):
        """ Draws the image (if visible) into the game offscreen.
        @param screen: Current game offscreen to draw in.
        @type screen: C{L{Window<bb_drawer.Window>}}
        """
        if not self.visible: return
        screen.blit(self.surface, (self.x, self.y))
