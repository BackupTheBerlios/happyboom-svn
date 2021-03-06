"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from client.item import Item
import random, pygame

class Building:
    """ Represents a building which is used as plat-form in the game.
    @ivar rect: Representation of the building.
    @type rect: C{pygame.Rect}
    @ivar color: Random color tuple of the building (Red, Green, Blue, Alpha).
    @type color: C{(int, int, int, int)}
    """
    
    def __init__(self, x, y, width, height):
        """ Building constructor.
        @param x: Building left abscisse.
        @type x: C{int}
        @param y: Building top ordonnee.
        @type y: C{int}
        @param width: Buiding width.
        @type width: C{int}
        @param height: Building height.
        @type height: C{int}
        """
        self.rect = pygame.Rect([x, y, width, height])
        self.color = (\
            random.randint(0,255), random.randint(0,255), \
            random.randint(0,255), 255,)

    def draw(self, screen):
        """ Drawing method called by C{BoomBoomDrawer}
        @param screen: Offscreen to draw in.
        @type screen: C{L{Window<bb_drawer.Window>}}
        """
        screen.surface.fill(self.color, self.rect)
        
class World(Item):
    """ Represents the ground of the game (collection of buildings).
    @ivar __buildings: Collection of buildings.
    @type __buildings: C{list<L{Building}>}
    """
    
    feature = "world"
    
    def __init__(self, id):
        """ World item constructor. """
        Item.__init__(self, id)
        self.__buildings = []
        self.registerEvent("world")

    def born(self):
        Agent.born(self)
        self.registerAction("world")

    def evt_world_create(self, data):
        """ World create event handler.
        @param event: Event with "world_create" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.__buildings = []
        rects = data.split(";")
        for rect in rects:
            x, y, w, h = rect.split(",")
            b = Building(int(x), int(y), int(w), int(h))
            self.__buildings.append(b)

    def draw(self, screen):
        """ Drawing method called by C{BoomBoomDrawer}
        @param screen: Offscreen to draw in.
        @type screen: C{L{Window<bb_drawer.Window>}}
        """
        for b in self.__buildings: b.draw(screen)
