"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from common import simple_event
from common.simple_event import EventListener
import bb_events
from bb_display import BoomBoomDisplay
from bb_input import BoomBoomInput
import thread, time, traceback, pygame

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
    
    def __init__(self, host, display_port, input_port, verbose=False, debug=False, max_fps=25):
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
        
        self.display = BoomBoomDisplay(host, display_port, verbose=verbose, debug=debug, max_fps=max_fps)
        self.input = BoomBoomInput(host, input_port, verbose=verbose, debug=debug)
        self.__verbose = verbose
        self.__stopped = False
        self.__stoplock = thread.allocate_lock()
        
        self.registerEvent(bb_events.stop)
        
    def start(self):
        """ Starts the game client."""
        if self.__verbose: print "[CLIENT] Starting client..."
        # Start pygame
        pygame.init()
        
        # Create thread for input and display
        thread.start_new_thread(self.thread_display, ())
        thread.start_new_thread(self.thread_input, ())

        quit = False
        while not quit:
            # Wait for Keyboard Interrupt
            time.sleep(0.100)
            self.__stoplock.acquire()
            quit = self.__stopped
            self.__stoplock.release()
        
    def stop(self):
        """  Stops the game client."""
        # Does not stop several times
        self.__stoplock.acquire()
        if self.__stopped:
            self.__stoplock.release()
            return
        self.__stopped = True
        self.__stoplock.release()
        
        if self.__verbose: print "[CLIENT] Stopping client..."
        self.display.stop()
        self.input.stop()
    
    def evt_game_Stop(self, event):
        """ Stop event handler.
        @param event: Event with "game_Stop" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.stop()
    
    def thread_display(self):
        """ Thread handler for the "display" part."""
        try:
            self.display.start()
        except:
            traceback.print_exc()
            self.stop()
        
    def thread_input(self):
        """ Thread handler for the "input" part."""
        try:
            self.input.start()
        except:
            traceback.print_exc()
            self.stop()
