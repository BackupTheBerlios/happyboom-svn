"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from common import simple_event
from common.simple_event import EventLauncher, EventListener
import bb_events
from bb_drawer import BoomBoomDrawer
from bb_constructor import BoomBoomConstructor
from net import io
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
    
    def __init__(self, host, port=12430, name="no name", verbose=False, debug=False, max_fps=25):
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
        self.drawer = BoomBoomDrawer(max_fps)
        self.host = host
        self.port = port
        self.name = name
        self.__protocol_version = "0.1.4"
        self.__io = io_tcp.IO_TCP()
        self.__verbose = verbose
        self.__io.verbose = verbose
        self.__debug = debug
        self.__io.debug = debug
        self.__stopped = False
        self.__stoplock = thread.allocate_lock()
        
        self.registerEvent(bb_events.askVersion)
        self.registerEvent(bb_events.askName)
        
    def start(self):
        """ Starts the display client : connection to the server, etc. """
        # Try to connect to server
        if self.__verbose: print "[DISPLAY] Trying to connect to server %s:%u" % (self.host, self.port)
        self.__io.on_connect = self.onConnect
        self.__io.on_disconnect = self.onDisconnect
        self.__io.on_new_packet = self.processPacket
        self.__io.on_lost_connection = self.onLostConnection
        self.__io.connect(self.host, self.port)
        thread.start_new_thread(self.__io.run_thread, ())
        
        BoomBoomConstructor()
        print "==== BoomBoom ===="
        self.drawer.start()
        
    def stop(self):
        """ Stops the display client : disconnection from the server, etc. """
        self.__stoplock.acquire()
        self.__stopped = True
        self.__stoplock.release()
        self.send("quit")
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

    def onDisconnect(self):
        """ Handler called on network disconnection. """
        print "[DISPLAY] Connection to server closed"
        self.launchEvent(bb_events.stop)

    def onLostConnection(self):
        """ Handler called on losting network connection. """
        print "[DISPLAY] Lost connection with server"
        self.launchEvent(bb_events.stop)
    
    def str2evt(self, str):
        """ Utility method to convert incomming network message string to local event.
        @param str: incomming network message string to convert.
        @type str: C{str}
        @return: A couple containing the event type and its optional argument for representing a local event to send.
        @rtype: C{(str, str)}
        """
        import re
        # Ugly regex to parse string
        r = re.compile("^([^:]+):([^:]+)(:(.*))?$")
        regs = r.match(str)
        if regs == None: return (None, None)
        role = regs.group(1)
        type = regs.group(2)
        if 2<regs.lastindex:
            arg = regs.group(4)
        else:
            arg = None
        event_type = "%s_%s" %(role, type)
        return (event_type, arg)
        
    def processPacket(self, new_packet):
        """ Processes incomming network packets (converts and launches local event).
        @param new_packet: incomming network packet.
        @type new_packet: C{net.io.packet.Packet}
        """
        event_type, arg = self.str2evt(new_packet.data)
        if event_type != None: 
            if self.__debug: print "Received message: type=%s arg=%s" %(event_type, arg)
            self.launchEvent(event_type, arg)
            
    def send(self, str):
        """ Sends a string to the network server.
        @param str: String to send.
        @type str: C{str}
        """
        p = io.Packet()
        p.writeStr(str)
        self.__io.send(p)
        
    def evt_agent_manager_AskVersion(self, event):
        """ AskVersion event handler (when server asks for client version).
        @param event: Event with "agent_manager_AskVersion" type
        @type event: C{L{common.simple_event.Event}}
        """
        self.send(self.__protocol_version)
        
    def evt_agent_manager_AskName(self, event):
        """ AskName event handler (when server asks for client name).
        @param event: Event with "agent_manager_AskName" type
        @type event: C{L{common.simple_event.Event}}
        """
        self.send(self.name)