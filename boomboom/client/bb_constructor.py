"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from happyboom.common.event import EventListener
import bb_events
from items import Sun, Projectile, Weapon, World, Character

class BoomBoomConstructor(EventListener):
    """ Constructs visual items when server requires creation. """
    def __init__(self):
        """ BoomBoomConstructor constructor. """
        EventListener.__init__(self, prefix="evt_")
        self.registerEvent("game")
        self.registerEvent(bb_events.create)
        self.registerEvent(bb_events.text)
        
    def evt_agent_manager_Create(self, event):
        """ Create event handler.
        @param event: Event with "agent_manager_Create" type.
        @type event: C{L{common.event.Event}}
        """
        arg = event.content.split(":")
        type = arg[0]
        id = int(arg[1])
        item = self.tryCreateItem(id, type)
        if item != None:
            event.source.send("yes")
            event.source.send(type)
            event.source.send(".")
        else:
            event.source.send("no")
        
    def tryCreateItem(self, id, type):
        """ Constructs an item of required type.
        @param id: Server id of the item.
        @type id: C{int}
        @param type: Type of item to construct.
        @type type: C{str}
        @return: The constructed item or C{None}, if the type does not exist.
        @rtype: C{L{BoomBoomItem}}
        """
        if type=="projectile":
            return Projectile()
        if type=="weapon":
            return Weapon()
        if type=="world":
            return World()
        if type=="character":
            return Character(id, "foo")
        return None
        
    def evt_game_start(self):
        """ Start event handler.
        @param event: Event with "game_Start" type.
        @type event: C{L{common.event.Event}}
        """
        Sun()
        
    def evt_agent_manager_Text(self, event):
        """ Text event handler.
        @param event: Event with "agent_manager_Text" type.
        @type event: C{L{common.event.Event}}
        """
        print "[DISPLAY] Server message: %s" %(event.content)
