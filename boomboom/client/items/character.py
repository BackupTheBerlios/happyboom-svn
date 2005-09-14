"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from client import bb_events
from client.bb_item import BoomBoomItem, VisualObject
import os.path
import pygame

class Character(BoomBoomItem):
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
    def __init__(self, id, name):
        """ Character item constructor.
        @param id:  Server item id.
        @type id: C{int}
        @param name: Character name.
        @type name: C{str}
        """
        BoomBoomItem.__init__(self)
        self.__x = None
        self.__y = None
        self.__id = id
        self.__name = name
        self.visual = VisualObject(os.path.join("data", "gorilla.png"))
        self.active = False
        self.registerEvent(bb_events.characterMove)
        self.registerEvent(bb_events.activeCharacter)
        
    def evt_character_move(self, event):
        """ Character move event handler.
        @param event: Event with "character_move" type.
        @type event: C{L{common.simple_event.Event}}
        """
        id, x, y = event.content.split(",")
        if self.__id != int(id): return
        self.__x = int(x)
        self.__y = int(y)
        self.visual.move(self.__x, self.__y)
        if self.active:
            self.launchEvent(bb_events.activeCharAbs, self.__x)
        
    def evt_game_active_character(self, event):
        """ Active character event handler.
        Adverts weapon the abscisse of the new active character.
        @param event: Event with "game_active_character" type.
        @type event: C{L{common.simple_event.Event}}
        """
        if self.__id == int(event.content):
            self.active = True
            if self.__x != None:
                self.launchEvent(bb_events.activeCharAbs, self.__x)