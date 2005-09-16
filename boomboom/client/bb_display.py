"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from happyboom.common.happyboom_protocol import HappyboomProtocol as Presentation
from happyboom.common.log import log
from happyboom.client.base_client import Client as BaseClient
from happyboom.common.event import EventListener
import bb_events
from bb_drawer import BoomBoomDrawer
from bb_constructor import BoomBoomConstructor
from happyboom.net.io import Packet

class BoomBoomDisplay(BaseClient, EventListener):
    """ Class which manages "display" part of the network connections.
    Also creates a drawer and a constuctor for "display" management.
    @ivar drawer: instance which draws screen game.
    @type drawer: C{L{BoomBoomDrawer}}
    @ivar host: Server hostname.
    @type host: C{str}
    @ivar port: Server port for "display"/"view" connection.
    @type port: C{int}
    @ivar name: Name of the client (as known by the server).
    @type name: C{str}
    """
    
    def __init__(self, arg):
        """ BoomBoomDisplay constructor.
        @param host: Server hostname.
        @type host: C{str}
        @param port: Server port for "display"/"view" connection.
        @type port: C{int}
        @param name: Name of the client (as known by the server).
        @type name: C{string}
        @param verbose: Verbose mode flag.
        @type verbose: C{bool}
        @param debug: Debug mode flag.
        @type debug: C{bool}
        @param max_fps: Maximal number of frames per second, for optimization.
        @type max_fps: C{int}
        """

        EventListener.__init__(self)
        BaseClient.__init__(self, arg)
        self.drawer = BoomBoomDrawer(arg.get("max_fps", 25))
        self.name = arg.get("name", "no name")
        #TODO: Support chat?
        self.gateway.features = ["game", "character", "projectile", "weapon", "world"]
#        if arg.get("server-log", False):
#            self.gateway.features.append("log")
        self.registerEvent("happyboom")

    def evt_happyboom_netSendMsg(self, feature, event, *args):
        self.send(feature, event, *args)

    def start(self):
        """ Starts the display client : connection to the server, etc. """
        print "==== BoomBoom ===="
        self.drawer.start()
        BaseClient.start(self)
        args = {"verbose": self.verbose}
        BoomBoomConstructor(args)
        self.drawer.mainLoop()
        
    def stop(self):
        """ Stops the display client : disconnection from the server, etc. """
        if not BaseClient.stop(self): return
        self.launchEvent("happyboom", "disconnection", self._io, u"Quit.")
        self._io.stop()
        if self.verbose: print "[CLIENT] Stopped"

# Wass used for stats
#    def setIoSendReceive(self, on_send, on_receive):
#        """ Set new handler functions for I/O network.
#        @param on_send: Handler called for sending data.
#        @type C{function}
#        @param on_receive: Handler called for receiving data.
#        @type C{function}
#        """
#        self._io.on_send = on_send
#        self._io.on_receive = on_receive
