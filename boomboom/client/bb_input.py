"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from happyboom.common.event import EventLauncher, EventListener
import bb_events
from net import io
from net import io_udp, io_tcp
from net import net_buffer
import thread, time, pygame

class BoomBoomInput(EventLauncher, EventListener):
    """ Class which manages "input" part of the network connections.
    @ivar host: Server hostname.
    @type host: C{str}
    @ivar port: Server port for "input" connection.
    @type port: C{int}
    @ivar name: Name of the client (as known by the server).
    @type name: C{str}
    @ivar __protocol_version: Current version of the protocol used by the client.
    @type __protocol_version: C{str}
    @ivar __io: Network input/output object using UDP protocole.
    @type __io: C{net.io_udp.IO_UDP}
    @ivar __recv_buffer: Network data reception buffer.
    @type __recv_buffer: C{net.net_buffer.NetBuffer}
    @ivar __verbose: Verbose mode flag.
    @type __verbose: C{bool}
    @ivar __debug: Debug mode flag.
    @type __debug: C{bool}
    @ivar __stopped: Stopped input client flag.
    @type __stopped: C{bool}
    @ivar __stoplock: Mutex for synchronizing __stopped.
    @type __stoplock: C{thread.lock}
    """
    
    def __init__(self, arg):
        """ BoomBoomInput constructor.
        @param host: Server hostname.
        @type host: C{str}
        @param port: Server port for "input" connection.
        @type port: C{int}
        @param name: Name of the client (as known by the server).
        @type name: C{string}
        @param verbose: Verbose mode flag.
        @type verbose: C{bool}
        @param debug: Debug mode flag.
        @type debug: C{bool}
        """

        EventLauncher.__init__(self)
        EventListener.__init__(self)
        self.weapon_angle = None
        self.weapon_strength = None
        self.registerEvent("weapon")

    def evt_weapon_setStrength(self, strength):
        self.weapon_strength = strength
        
    def evt_weapon_setAngle(self, angle):
        self.weapon_angle = angle
        
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

    def weapon_setStrengthDelta(self, delta):
        self.launchEvent("happyboom", "network", \
            "weapon", "askSetStrength", self.weapon_strength + delta)

    def weapon_setAngleDelta(self, delta):
        self.launchEvent("happyboom", "network", \
            "weapon", "askSetAngle", self.weapon_angle + delta)

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
