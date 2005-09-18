from curses_client.item import Item
from curses_client.curses_tools import convertXY

class Character(Item):
    feature = "character"
    
    def __init__(self, id):
        Item.__init__(self)
        self.x, self.y = None, None
        self.__id = id
        self.__name = "unamed%s"%id
        self.active = False
        self.registerEvent("character")
        
    def evt_character_move(self, id, x, y):
        if self.__id != id: return
        self.x, self.y = (x, y)
        
    def draw(self, screen):
        if self.x == None: return
        x, y = convertXY(screen, int(self.x), int(self.y))
        screen.addstr(y, x, "oo")
        screen.addstr(y+1, x-1, "(ww)"+" "*screen.getmaxyx()[1])
