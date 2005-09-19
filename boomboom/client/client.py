"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from happyboom.common.event import EventListener
from happyboom.common.log import log
from happyboom.common.thread import getBacktrace
from happyboom.common import protocol
from happyboom.client.base_client import Client as Happyboom
from display import Display
from input import Input
import thread, time
import curses_tools

class Client(Happyboom, EventListener):
    """ The main class of the client of BoomBoom.
    @ivar display: Display manager of the game.
    @type display: C{L{BoomBoomDisplay}}
    @ivar input: Input manager of the game.
    @type input: C{L{BoomBoomInput}}
    @ivar __verbose: Verbose mode flag.
    @type __verbose: C{bool}
    @ivar __stopped: Stopped game flag.
    @type __stopped: C{bool}
    @ivar __stoplock: Mutex for synchronizing __stopped.
    @type __stoplock: C{thread.lock}
    """
    
    def __init__(self, args):
        """ BoomBoomClient constructor.
        @param host: Server hostname.
        @type host: C{str}
        @param display_port: Server port for "display"/"view" connection.
        @type display_port: C{int}
        @param input_port: Server port for "input" connection.
        @type input_port: C{int}
        @param verbose: Verbose mode flag.
        @type verbose: C{bool}
        @param debug: Debug mode flag.
        @type debug: C{bool}
        @param max_fps: Maximal number of frames per second, for optimization.
        @type max_fps: C{int}
        """
        args["protocol"] = protocol.loadProtocol("protocol.xml")
        args["features"] = ["game"] # Constant features
        
        Happyboom.__init__(self, args)
        EventListener.__init__(self, prefix="evt_")
        
        self.display = Display(args)
        self.input = Input(args)
        self.__verbose = args.get("verbose", False)
        self.registerEvent("happyboom")        
        self.registerEvent("game")
        
    def start(self):
        """ Starts the game client."""
        if self.__verbose:
            log.info("[BOOMBOOM] Starting client...")
        Happyboom.start(self)
        # Create thread for display
        thread.start_new_thread(self.displayThread, ())
        
        quit = False
        while not quit:
            self.input.process()
            time.sleep(0.100)
            quit = self.stopped
        
    def stop(self):
        """  Stops the game client."""
        if self.__verbose:
            log.info("[BOOMBOOM] Stopping client...")
        Happyboom.stop(self)
        self.launchEvent("happyboom", "disconnection", self._io, u"Quit.")
        self.display.stop()
    
    def evt_game_stop(self):        
        self.stop()
        
    def evt_happyboom_stop(self):
        """ Stop event handler.
        """
        self.stop()
    
    def displayThread(self):
        """ Thread handler for the "display" part."""
        try:
            self.display.start()
        except Exception, msg:
            bt = getBacktrace()
            log.error("EXCEPTION IN DISPLAY THREAD:\n%s\n%s" % (msg, bt))
        try:
            self.stop()
        except Exception, msg:
            bt = getBacktrace()
            log.error("EXCEPTION (2) IN DISPLAY THREAD:\n%s\n%s" % (msg, bt))
