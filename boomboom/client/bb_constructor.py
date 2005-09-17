"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from happyboom.common.event import EventListener
from happyboom.common.log import log
import bb_events

class BoomBoomConstructor(EventListener):
    """ Constructs visual items when server requires creation. """
    def __init__(self, arg):
        """ BoomBoomConstructor constructor. """
        EventListener.__init__(self, prefix="evt_")
        self.verbose = arg.get("verbose", False)
        self.registerEvent("happyboom")
        self.registerEvent("game")
        self.textmode = arg["textmode"]
        self.args = arg
        
    def evt_happyboom_doCreateItem(self, type, id):
        """ Create event handler.
        @param event: Event with "agent_manager_Create" type.
        @type event: C{L{common.event.Event}}
        """
        if self.verbose:
            log.info("Try to create object %s ..." % type)
        if type=="projectile":
            if self.textmode:
                from items.projectile_curses import Projectile
            else:
                from items.projectile import Projectile
            Projectile(self.args)
        if type=="weapon":
            if self.textmode:
                from items.weapon_curses import Weapon 
            else:
                from items.weapon import Weapon
            Weapon(self.args)
        if type=="log":
            from items import LogItem
            LogItem()
        if type=="world":
            if self.textmode:
                from items.world_curses import World
            else:
                from items.world import World
            World(self.args)
        if type=="character":
            if self.textmode:
                from items.character_curses import Character
            else:
                from items.character import Character
            Character(id, "foo", self.args)
        
    def evt_game_start(self):
        """ Start event handler.
        @param event: Event with "game_Start" type.
        @type event: C{L{common.event.Event}}
        """
        if not self.textmode:
            from items import Sun
            Sun()
        
    def evt_agent_manager_Text(self, event):
        """ Text event handler.
        @param event: Event with "agent_manager_Text" type.
        @type event: C{L{common.event.Event}}
        """
        print "[CLIENT] Server message: %s" %(event.content)
