from client.bb_input import BoomBoomInput as BaseInput
import pygame                

class BoomBoomInput(BaseInput):
    def __init__(self, arg):
        BaseInput.__init__(self, arg)
#        import pygame

    def process(self):
        for input_event in pygame.event.get():
            self.process_event(input_event)
           
    def process_event(self, event):
        """ Manages when a pygame event is caught.
        @param event: Pygame event.
        @type event: C{pygame.Event}
        """
        if event.type == pygame.KEYDOWN: 
            # q, Q or escape: quit
            if event.unicode in (u'q', u'Q') or event.key == 27:
                self.launchEvent("game", "stop")
        # Quit event: quit
        elif event.type in (pygame.QUIT, ):
            self.launchEvent("game", "stop")
    
        #character = self.client.view.getActiveCharacter()
        #if character != None: self.process_event_active(character, event)
        self.process_event_active(event)

    def process_event_active(self, event):
        """ Manages when a pygame event is caught and interact with the server.
        @param event: Pygame event.
        @type event: C{pygame.Event}
        """
        #delta_angle = -30
        if event.type == pygame.KEYDOWN: 
            # arrow keys: move character
            if event.key == 32:
                self.launchEvent("happyboom", "netSendMsg", "weapon", "shoot")
            elif event.key == 275:
                self.weapon_setStrengthDelta(10) # RIGHT 
            elif event.key == 273:
                self.weapon_setAngleDelta(10) # UP
            elif event.key == 274:
                self.weapon_setAngleDelta(-10) # DOWN
            elif event.key == 276:
                self.weapon_setStrengthDelta(-10) # LEFT
