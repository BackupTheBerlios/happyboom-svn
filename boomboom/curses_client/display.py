from happyboom.common.event import EventListener
import bb_events
import curses, time

class BoomBoomDrawer(EventListener):
    """ Manages the drawing of the screen game (double buffered) in a display loop.
    @ivar __screen: Current drawed offscreen.
    @type __screen: C{{Window}}
    @ivar __frameTime: Minimum time to draw a frame.
    @type __frameTime: C{float}
    @ivar __items: Objects which have graphical content to draw (visual items) genered by visible item events.
    @type __items: C{list<L{BoomBoomItem}>}
    """
    
    def __init__(self, args):
        """ BoomBoomDrawer constructor.
        @param max_fps: Maximal number of frames per second, for optimization.
        @type max_fps: C{int}
        """
        EventListener.__init__(self, prefix="evt_")
        # Current offscreen
        self.__screen = None
        max_fps = args.get("max_fps", 25)
        self.__frameTime = 1.0 / max_fps
        self.__items = []
        self.registerEvent("graphical")
        self.window = args["window"]
    
    def start(self):
        pass
        
    def mainLoop(self):
        """ Display loop. """
        while True:
            live_begin = time.time()
            
            # Clearing screen
            self.window.clear()

            # Drawing each items
            for item in self.__items:
                item.draw()

            # Displaying offscreen 
            self.window.refresh()
            
            delay = time.time() - live_begin
            if delay < self.__frameTime:
                delay = self.__frameTime - delay
                time.sleep(delay)
        
    def evt_graphical_item(self, item):
        """ active item event handler.
        @param event: Event with "graphical_item" type.
        @type event: C{L{common.simple_event.Event}}
        """
        if item not in self.__items:
            self.__items.append(item)
