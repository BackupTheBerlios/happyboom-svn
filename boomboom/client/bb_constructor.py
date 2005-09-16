"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from happyboom.common.event import EventListener
from happyboom.common.log import log
import bb_events
from items import Sun, Projectile, Weapon, World, Character, LogItem

class BoomBoomConstructor(EventListener):
    """ Constructs visual items when server requires creation. """
    def __init__(self, arg):
        """ BoomBoomConstructor constructor. """
        EventListener.__init__(self, prefix="evt_")
        self.verbose = arg.get("verbose", False)
        self.registerEvent("happyboom")
        self.registerEvent("game")
        
    def evt_happyboom_doCreateItem(self, type, id):
        """ Create event handler.
        @param event: Event with "agent_manager_Create" type.
        @type event: C{L{common.event.Event}}
        """
        if self.verbose:
            log.info("Try to create object %s ..." % type)
        if type=="projectile":
            Projectile()
        if type=="weapon":
            Weapon()
        if type=="log":
            LogItem()
        if type=="world":
            World()
        if type=="character":
            Character(id, "foo")
        
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
        print "[CLIENT] Server message: %s" %(event.content)
