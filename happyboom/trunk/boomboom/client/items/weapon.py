"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from client import bb_events
from client.bb_item import BoomBoomItem
import pygame

class Weapon(BoomBoomItem):
    """ Represents the weapon parameters controlled by the player.
    @ivar __angle: Projection angle.
    @type __angle: C{int}
    @ivar __strength: Projection strength.
    @type __strength: C{int}
    @ivar __font: Font used to print parameters.
    @type __font: C{pygame.Font}
    @ivar __font_color: Letter color tuple used to print parameters (Red, Green, Blue, Alpha).
    @type __font_color: C{(int, int, int, int)}
    @ivar __font_background: Background color tuple used to print parameters (Red, Green, Blue, Alpha).
    @type __font_background: C{(int, int, int, int)}
    @ivar __x: Item abscisse.
    @type __x: C{int}
    @ivar __y: Item ordonnee.
    @type __y: C{int}
    """
    def __init__(self):
        """ Weapon item constructor. """
        BoomBoomItem.__init__(self)
        self.__angle = None 
        self.__strength = None
        fontname = pygame.font.get_default_font()
        self.__font = pygame.font.SysFont(fontname, 14)
        self.__font_color = (255,255,255,255)
        self.__font_background = (0,0,0,0)
        self.__y = 10
        self.__x = 10
        self.registerEvent(bb_events.weaponStrength)
        self.registerEvent(bb_events.weaponAngle)
        self.registerEvent(bb_events.activeCharAbs)
        
    def evt_weapon_force(self, event):
        """ Weapon strength event handler.
        @param event: Event with "weapon_force" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.__strength = int(event.content)
        
    def evt_weapon_angle(self, event):
        """ Weapon angle event handler.
        @param event: Event with "weapon_angle" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.__angle = int(event.content)
        
    def evt_active_character_abscisse(self, event):
        """ Active character abcsisse event handler.
        @param event: Event with "active_character_abscisse" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.__x = int(event.content)
        
    def draw(self, screen):
        """ Drawing method called by C{BoomBoomDrawer}
        @param screen: Offscreen to draw in.
        @type screen: C{L{Window<bb_drawer.Window>}}
        """
        if self.__angle == None: return
        if self.__strength == None: return
        txt = "Angle: %s  Strength: %s" % (self.__angle, self.__strength)
        surface = self.__font.render(txt, True, self.__font_color, self.__font_background)
        screen.blit(surface, (self.__x,self.__y))