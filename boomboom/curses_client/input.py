from generic_input import Input as BaseInput
import curses
                
class Input(BaseInput):
    def __init__(self, arg):
        BaseInput.__init__(self, arg)
        self.window = arg["window"]

    def process(self):
        self.window.nodelay(True)
        key = self.window.getch()
        self.process_key(key)
           
    def process_key(self, key):
        if key == -1: return
        keyname = curses.keyname(key)
        if keyname in ('q', 'Q'):
            self.launchEvent("game", "stop")
#            return
    
        if key == 32: # space
            self.launchEvent("happyboom", "network", "weapon", "shoot")
        elif key == curses.KEY_RIGHT:
            self.weapon_setStrengthDelta(10)
        elif key == curses.KEY_UP:
            self.weapon_setAngleDelta(10)
        elif key == curses.KEY_DOWN:
            self.weapon_setAngleDelta(-10)
        elif key == curses.KEY_LEFT:
            self.weapon_setStrengthDelta(-10)
