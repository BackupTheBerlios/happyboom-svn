"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from happyboom.common.event import EventListener
from happyboom.common.log import log
from happyboom.common.thread import getBacktrace
import bb_events
import thread, time, traceback
import curses_tools

class BoomBoomClient(EventListener):
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
    
    def __init__(self, display, arg):
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
        EventListener.__init__(self, prefix="evt_")
        
        self.display = display
        if not arg.get("textmode", False):
            from bb_input_pygame import BoomBoomInput
        else:
            log.use_print = False
            log.on_new_message = curses_tools.onLogMessage
            curses_tools.window = arg["window"]
            from bb_input_curses import BoomBoomInput
        self.input = BoomBoomInput(arg)
        self.__verbose = arg.get("verbose", False)
        self.__stopped = False
        self.__stoplock = thread.allocate_lock()
        self.args = arg        
        self.registerEvent("game")
        
    def start(self):
        """ Starts the game client."""
        if self.__verbose:
            log.info("[CLIENT] Starting client...")
        
        # Create thread for input and display
        thread.start_new_thread(self.thread_display, ())

        quit = False
        while not quit:
            self.input.process()
            time.sleep(0.100)
            quit = self.is_stopped
        
    def stop(self):
        """  Stops the game client."""
        # Does not stop several times
        self.__stoplock.acquire()
        if self.__stopped:
            self.__stoplock.release()
            return
        self.__stopped = True
        self.__stoplock.release()
        
        if self.__verbose:
            log.info("[CLIENT] Stopping client...")
        self.display.stop()
    
    def evt_game_stop(self):
        """ Stop event handler.
        @param event: Event game.stop()
        @type event: C{L{common.simple_event.Event}}
        """
        self.stop()
    
    def thread_display(self):
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
        
    def __isStopped(self):
        self.__stoplock.acquire()
        stop = self.__stopped
        self.__stoplock.release()
        return stop
    is_stopped = property(__isStopped)
