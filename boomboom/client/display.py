"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from happyboom.common.happyboom_protocol import HappyboomProtocol as Presentation
from happyboom.common.log import log
from happyboom.common.event import EventListener
from items import Sun
import thread, pygame, time

class Display(EventListener):
    """ Class which manages "display" part of the network connections.
    Also creates a drawer and a constuctor for "display" management.
    @ivar drawer: instance which draws screen game.
    @type drawer: C{L{BoomBoomDrawer}}
    @ivar host: Server hostname.
    @type host: C{str}
    @ivar port: Server port for "display"/"view" connection.
    @type port: C{int}
    @ivar name: Name of the client (as known by the server).
    @type name: C{str}
    """
    
    def __init__(self, args):
        """ BoomBoomDisplay constructor.
        @param host: Server hostname.
        @type host: C{str}
        @param port: Server port for "display"/"view" connection.
        @type port: C{int}
        @param name: Name of the client (as known by the server).
        @type name: C{string}
        @param verbose: Verbose mode flag.
        @type verbose: C{bool}
        @param debug: Debug mode flag.
        @type debug: C{bool}
        @param max_fps: Maximal number of frames per second, for optimization.
        @type max_fps: C{int}
        """

        EventListener.__init__(self)
        self.registerEvent("graphical")
        # Current offscreen
        self._screen = None
        max_fps = args.get("max_fps", 25)
        self._frameTime = 1.0 / max_fps
        self._items = []
        self.__stopped = False
        self.__stoplock = thread.allocate_lock()

    def start(self):
        """ Creates game window and starts display loop. """
        self._screen = Window(640, 350)
        self._screen.background_color = (0, 0, 168)
        Sun()
        self.mainLoop()
        
    def stop(self):
        """ Stops the display loop. """
        # Does not stop several times
        self.__stoplock.acquire()
        if self.__stopped:
            self.__stoplock.release()
            return False
        self.__stopped = True
        self.__stoplock.release()
        
    def mainLoop(self):
        """ Display loop. """
        while not self.stopped:
            live_begin = time.time()
            
            # Clearing screen
            self._screen.surface.fill(self._screen.background_color)
            # Drawing each items
            if len(self._items) == 0:
                fontname = pygame.font.get_default_font()
                font = pygame.font.SysFont(fontname, 64)
                font_color = (255,255,0,255)
                #font_background = (0,0,0,0)
                surface = font.render(" Not connected to server...", True, font_color)
                self._screen.blit(surface, (0,0))
            for item in self._items:
                item.draw(self._screen)
            # Displaying offscreen
            pygame.display.flip()
            
            delay = time.time() - live_begin
            if delay < self._frameTime:
                delay = self._frameTime - delay
                time.sleep(delay)
        
    def evt_graphical_item(self, item):
        """ active item event handler.
        @param event: Event with "graphical_item" type.
        @type event: C{L{common.simple_event.Event}}
        """
        if item not in self._items:
            self._items.append(item)
    
    def __isStopped(self):
        self.__stoplock.acquire()
        stop = self.__stopped
        self.__stoplock.release()
        return stop
    stopped = property(__isStopped)
        
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
            self.surface = pygame.display.set_mode((width,height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.pos = (0,0)
        self.view_pos = (0,0)
        self.scale = 1
        self.border_color = (255, 255, 255)
        self.background_color = (0, 0, 0)

    def blit(self, surface, pos):
        new_pos = (pos[0] - self.view_pos[0], pos[1] - self.view_pos[1],)
        self.surface.blit(surface, new_pos)