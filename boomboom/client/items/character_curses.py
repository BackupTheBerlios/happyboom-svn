from client.bb_item import BoomBoomItem
from client.curses_tools import convertXY

class Character(BoomBoomItem):
    def __init__(self, id, name, args):
        BoomBoomItem.__init__(self)
        self.x, self.y = None, None
        self.__id = id
        self.__name = name
        self.active = False
        self.registerEvent("character")
        self.window = args["window"]
        
    def evt_character_move(self, id, x, y):
        if self.__id != id: return
        self.x, self.y = convertXY(x, y)
        
    def draw(self):
        if self.x == None: return
        self.window.addstr(self.y, self.x, "Gorilla")
