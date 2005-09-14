"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from happyboom.common.presentation import Presentation
from happyboom.common.simple_event import EventLauncher, EventListener
import bb_events
from bb_drawer import BoomBoomDrawer
from bb_constructor import BoomBoomConstructor
from net import io
from happyboom.net.io import Packet
from net import io_udp, io_tcp
import thread

class BoomBoomDisplay(EventLauncher, EventListener):
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
    @ivar __protocol_version: Current version of the protocol used by the client.
    @type __protocol_version: C{str}
    @ivar __io: Network input/output object using UDP protocole.
    @type __io: C{net.io_udp.IO_UDP}
    @ivar __verbose: Verbose mode flag.
    @type __verbose: C{bool}
    @ivar __debug: Debug mode flag.
    @type __debug: C{bool}
    @ivar __stopped: Stopped display client flag.
    @type __stopped: C{bool}
    @ivar __stoplock: Mutex for synchronizing __stopped.
    @type __stoplock: C{thread.lock}
    """
    
    def __init__(self, protocol, arg):
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
        EventLauncher.__init__(self)
        EventListener.__init__(self, prefix="evt_")
        self.launchEvent("x")
        self.presentation = Presentation(protocol, False)
        self.drawer = BoomBoomDrawer(arg.get("max_fps", 25))
        self.host = arg.get("host", "localhost")
        self.port = arg.get("port", 12430)
        self.name = arg.get("name", "no name")
        self.__protocol = protocol
        self.__io = io_tcp.IO_TCP()
        self.__verbose = arg.get("verbose", False)
        self.__io.verbose = self.__verbose
        self.__debug = arg.get("debug", False)
        self.__io.debug = self.__debug
        self.__stopped = False
        self.__stoplock = thread.allocate_lock()
        
        self.registerEvent(bb_events.shoot)
        
    def start(self):
        """ Starts the display client : connection to the server, etc. """
        # Try to connect to server
        if self.__verbose: print "[DISPLAY] Trying to connect to server %s:%u" % (self.host, self.port)
        self.__io.on_connect = self.onConnect
        self.__io.on_connection_fails = self.onConnectionFails
        self.__io.on_disconnect = self.onDisconnect
        self.__io.on_new_packet = self.presentation.processPacket
        self.__io.on_lost_connection = self.onLostConnection
        self.__io.connect(self.host, self.port)
        if not self.__io.is_ready: return
        thread.start_new_thread(self.__io.run_thread, ())
    
        BoomBoomConstructor()
        self.__io.send(self.presentation.connectionPacket())
        print "==== BoomBoom ===="
        self.drawer.start()
        
    def stop(self):
        """ Stops the display client : disconnection from the server, etc. """
        self.__stoplock.acquire()
        self.__stopped = True
        self.__stoplock.release()
        # TODO: clean "bye"
        packet = self.presentation.disconnectionPacket(u"Quit.")
        self.__io.send(packet)
        self.__io.stop()
        if self.__verbose: print "[DISPLAY] Stopped"
        
    def setIoSendReceive(self, on_send, on_receive):
        """ Set new handler functions for I/O network.
        @param on_send: Handler called for sending data.
        @type C{function}
        @param on_receive: Handler called for receiving data.
        @type C{function}
        """
        self.__io.on_send = on_send
        self.__io.on_receive = on_receive
        
    def onConnect(self):
        """ Handler called on network connection. """
        if self.__verbose: print "[DISPLAY] Connected to server"
        
    def onConnectionFails(self):
        """ Handler called when network connection fails. """
        print "[DISPLAY] Fail to connect to the server"

    def onDisconnect(self):
        """ Handler called on network disconnection. """
        print "[DISPLAY] Connection to server closed"
        self.launchEvent(bb_events.stop)

    def onLostConnection(self):
        """ Handler called on losting network connection. """
        print "[DISPLAY] Lost connection with server"
        self.launchEvent(bb_events.stop)
    
    def send(self, feature, event, *args):
        """ Sends a string to the network server.
        @param str: String to send.
        @type str: C{str}
        """
        data = self.__protocol.createMsg(feature, event, *args)
        data = self.presentation.sendMsg(data)
        self.__io.send(Packet(data))

    def evt_x(self, event):
        print "x"
        
    def evt_weapon_shoot(self, event):
        print "Shoot aussi"
        self.send("weapon", "shoot")
