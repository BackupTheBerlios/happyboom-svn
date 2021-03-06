"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from client.item import Item, VisualObject
import os.path

class Character(Item):
    """ Represents a monkey character controlled by the player.
    @ivar visual: Graphical object containing data and transformations
    @type visual: C{L{VisualObject}}
    @ivar __x: Item abscisse.
    @type __x: C{int}
    @ivar __y: Item ordonnee.
    @type __y: C{int}
    @ivar __id: Server item id.
    @type __id: C{int}
    @ivar __name: Name of the player controlling the character (as known by the server).
    @type __name: C{str}
    """
    feature = "character"
    
    def __init__(self, id):
        """ Character item constructor.
        @param id:  Server item id.
        @type id: C{int}
        @param name: Character name.
        @type name: C{str}
        """
        Item.__init__(self, id)
        self.__x = None
        self.__y = None
        self.__id = id
        self.__name = "unamed%s" %id
        self.visual = VisualObject(os.path.join("data", "gorilla.png"))
        self.active = False
        self.registerEvent("character")
        
    def evt_character_move(self, id, x, y):
        """ Character move event handler.
        @param event: Event with "character_move" type.
        @type event: C{L{common.simple_event.Event}}
        """
        if self.__id != id: return
        self.__x = x
        self.__y = y
        self.visual.move(self.__x, self.__y)
    
    def eventPerformed(self, event):
        if event.event == "move":
            raise Exception(event)
    
    def evt_character_name(self, id, name):
        self.__name = name
