from net import io_udp
from common.happyboom_protocol import HappyboomProtocol
from common.event import EventLauncher, EventListener
import struct

class Client(object, EventListener, EventLauncher):
    
    def __init__(self, args):
        EventLauncher.__init__(self)
        EventListener.__init__(self) # TODO : Fix me (with good arguments)
        self.host = args.get("host", "127.0.0.1")
        self.port = args.get("port", 12430)
        self.verbose = args.get("verbose", False)
        self.debug = args.get("debug", False)
        protocol = args.get("protocol", None)
        self.__io = io_udp.IO_UDP()
        self.__verbose = verbose
        self.__io.verbose = verbose
        self.__debug = debug
        self.__io.debug = debug
        self.__stopped = False
        self.__stoplock = thread.allocate_lock()
        
        self.signature = None
        self.presentation = common.HappyboomProtocol(protocol)
        self.gateway = Gateway()
        
    def start(self):
        """ Starts the client : connection to the server, etc. """
        # Try to connect to server
        if self.__verbose: print "[HAPPYBOOM] Trying to connect to server %s:%u" % (self.host, self.port)
        self.__io.on_connect = self.onConnect
        self.__io.on_connection_fails = self.onConnectionFails
        self.__io.on_disconnect = self.onDisconnect
        self.__io.on_new_packet = self.gateway.processPacket
        self.__io.on_lost_connection = self.onLostConnection
        self.__io.connect(self.host, self.port)
        if not self.__io.is_ready: return
        thread.start_new_thread(self.__io.run_thread, ())
        
    def stop(self):
        """ Stops the display client : disconnection from the server, etc. """
        # Does not stop several times
        self.__stoplock.acquire()
        if self.__stopped:
            self.__stoplock.release()
            return
        self.__stopped = True
        self.__stoplock.release()
        
        self.send("quit")
        self.__io.stop()
        if self.__verbose: print "[HAPPYBOOM] Stopped"
        
    def __isStopped(self):
        self.__stoplock.acquire()
        stop = self.__stopped
        self.__stoplock.release()
        return stop
    stopped = property(__isStopped)
    
    def onConnect(self):
        """ Handler called on network connection. """
        if self.__verbose: print "[HAPPYBOOM] Connected to server"
        
    def onConnectionFails(self):
        """ Handler called when network connection fails. """
        print "[HAPPYBOOM] Fail to connect to the server"

    def onDisconnect(self):
        """ Handler called on network disconnection. """
        print "[HAPPYBOOM] Connection to server closed"
        self.launchEvent("happyboom", "stop")

    def onLostConnection(self):
        """ Handler called on losting network connection. """
        print "[HAPPYBOOM] Lost connection with server"
        self.launchEvent("happyboom", "stop")
        
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
        
class Gateway(EventLauncher, EventListener):
    def __init__(self):
        EventLauncher.__init__(self)
        EventListener.__init__(self, "evt_")
        self.launchEvent("happyboom", "register", "connection", self.processConnection)
        self.launchEvent("happyboom", "register", "disconnection", self.processDisconnection)
        self.launchEvent("happyboom", "register", "create_item", self.processConnection)
        self.launchEvent("happyboom", "register", "destroy_item", self.processConnection)
        self.launchEvent("happyboom", "register", "recv_event", self.processConnection)
        self.registerEvent("happyboom")
        
    def processConnection(self, version, signature):
        self.launchEvent("happyboom", "signature", signature)
        
    def processDisconnection(self, reason):
        self.launchEvent("happyboom", "stop", reason)
    
    def processCreateItem(self, feature, id):
        self.launchEvent(feature, "new", id)
    
    def processDestroyItem(self, id):
        self.launchEvent(feature, "delete", id)
    
    def processEvent(self, feature, event, args):
        self.launchEvent(feature, event, *args)

    def evt_happyboom_features(self, feature):
        if feature not in self.features:
            self.features.append(feature)
            self.registerEvent(feature)
            
    def processEvent(self, event):
        if self.type != "happyboom":
            self.launchEvent("happyboom", "send", *event.content)
            
    