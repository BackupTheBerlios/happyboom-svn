"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from client.item import Item

class Weapon(Item):
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
    
    feature = "weapon"
    
    def __init__(self, id):
        """ Weapon item constructor. """
        Item.__init__(self, id)
        self.__angle = None 
        self.__strength = None
        fontname = pygame.font.get_default_font()
        self.__font = pygame.font.SysFont(fontname, 14)
        self.__font_color = (255,255,255,255)
        self.__font_background = (0,0,0,0)
        self.x, self.y = (None, 10)
        self.character_pos = {}
        self.active_character = None
        self.registerEvent("weapon")
        self.registerEvent("character")

    def evt_weapon_setStrength(self, strength):
        """ Weapon strength event handler.
        @param event: Event with "weapon_force" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.__strength = strength
        
    def evt_weapon_setAngle(self, angle):
        """ Weapon angle event handler.
        @param event: Event with "weapon_angle" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.__angle = angle 

    def evt_character_move(self, id, x, y):
        self.character_pos[id] = (x, y,)
        self.updateX()
        
    def evt_character_activate(self, id):
        """ Active character abcsisse event handler.
        @param event: Event with "active_character_abscisse" type.
        @type event: C{L{common.simple_event.Event}}
        """
        self.active_character = id
        self.updateX()
               
    def draw(self, screen):
        """ Drawing method called by C{BoomBoomDrawer}
        @param screen: Offscreen to draw in.
        @type screen: C{L{Window<bb_drawer.Window>}}
        """
        if self.__angle == None: return
        if self.__strength == None: return
        if self.x == None: return
        txt = "Angle: %s  Strength: %s" % (self.__angle, self.__strength)
        surface = self.__font.render(txt, True, self.__font_color, self.__font_background)
        screen.blit(surface, (self.x,self.y))

    def updateX(self):
        if self.active_character==None: return
        pos = self.character_pos.get(self.active_character, None)
        if pos != None: self.x = pos[0]
