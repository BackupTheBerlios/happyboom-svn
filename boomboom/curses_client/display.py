from happyboom.common.event import EventListener
from happyboom.common.log import log
import curses, time, thread, item

class Display(EventListener):
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
        self.__stopped = False
        self.__stoplock = thread.allocate_lock()
        self.__itemlock = thread.allocate_lock()
    
    def start(self):
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
        for i in range(1,7):
            curses.init_pair(i, i, curses.COLOR_BLACK)
        while not self.stopped:
            live_begin = time.time()
            
            # Clearing screen
            self.window.clear()

            # Drawing each items
            items = self.getItems()
            for item in items[:]:
                if item.__class__.__name__ == "Projectile":
                    item.draw(self.window)
                    items.remove(item)
            for item in items[:]:
                if item.__class__.__name__ == "Character":
                    item.draw(self.window)
                    items.remove(item)
            for item in items[:]:
                item.draw(self.window)
                items.remove(item)

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
            self.addItem(item)
            
    def __isStopped(self):
        self.__stoplock.acquire()
        stop = self.__stopped
        self.__stoplock.release()
        return stop
    stopped = property(__isStopped)
    
    def getItems(self):
        self.__itemlock.acquire()
        items = self.__items[:]
        self.__itemlock.release()
        return items
    def addItem(self, item):
        self.__itemlock.acquire()
        self.__items.append(item)
        self.__itemlock.release()