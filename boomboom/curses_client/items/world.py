from curses_client.item import Item
from curses_client.curses_tools import convertXY
import random, curses

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
        self.x, self.y = x,y
        self.width, self.height = width, height
        self.color = None

    def draw(self, screen):
        """ Drawing method called by C{BoomBoomDrawer}
        @param screen: Offscreen to draw in.
        @type screen: C{L{Window<bb_drawer.Window>}}
        """
        if self.color == None:
            self.color = random.randint(0, 6)
        x, y = convertXY(screen, int(self.x), int(self.y))
        w, h = convertXY(screen, int(self.width), int(self.height))
        for line in range(y, y+h):
            screen.addstr(line, x, "#" * w, curses.color_pair(self.color))
        
class World(Item):
    """ Represents the ground of the game (collection of buildings).
    @ivar __buildings: Collection of buildings.
    @type __buildings: C{list<L{Building}>}
    """
    feature = "world"
    
    def __init__(self, id):
        """ World item constructor. """
        Item.__init__(self)
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
        #maxy, maxx = self.window.getmaxyx()
        for rect in rects:
            x, y, w, h = rect.split(",")
            #x, y = convertXY(int(x), int(y))
            #w, h = convertXY(int(w), int(h))
            b = Building(x, y, w, h)
            self.__buildings.append(b)

    def draw(self, screen):
        """ Drawing method called by C{BoomBoomDrawer}
        @param screen: Offscreen to draw in.
        @type screen: C{L{Window<bb_drawer.Window>}}
        """
        for b in self.__buildings: b.draw(screen)
