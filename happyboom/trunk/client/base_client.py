from happyboom.common.happyboom_protocol import HappyboomProtocol
from happyboom.common.protocol import ProtocolException
from happyboom.common.log import log
from happyboom.common.event import EventLauncher, EventListener
from happyboom.net.io.packet import Packet
from happyboom.net.io_tcp.tcp import IO_TCP
import struct, string
import thread

class Client(object, EventListener, EventLauncher):
    """
    Base HappyBoom client.
    @ivar __stopped: Stopped display client flag.
    @type __stopped: C{bool}
    @ivar __stoplock: Mutex for synchronizing __stopped.
    @type __stoplock: C{thread.lock}
    @ivar _io: Network input/output object using UDP protocole.
    @type _io: C{net.io_udp.IO_UDP}
    @ivar verbose: Verbose mode flag.
    @type verbose: C{bool}
    @ivar debug: Debug mode flag.
    @type debug: C{bool}
    """
    
    def __init__(self, args):
        EventListener.__init__(self) # TODO : Fix me (with good arguments)
        EventLauncher.__init__(self)
        self.host = args.get("host", "127.0.0.1")
        self.port = args.get("port", 12430)
        self.verbose = args.get("verbose", False)
        self.debug = args.get("debug", False)
        protocol = args.get("protocol", None)
        self._io = IO_TCP()
        self._io.verbose = False # self.verbose
        self._io.debug = False # self.debug
        self.__stopped = False
        self.__stoplock = thread.allocate_lock()
        
        self.signature = None
        self.presentation = HappyboomProtocol(protocol, args)
        self.gateway = Gateway(protocol, args)
        self.registerEvent("happyboom")

    def evt_happyboom_network(self, feature, event, *args):
        self.send(feature, event, *args)

    def send(self, feature, event, *args):
        """ Sends a string to the network server.
        @param str: String to send.
        @type str: C{str}
        """
        data = self.presentation.protocol.createMsg(feature, event, *args)
        self.launchEvent("happyboom", "event", (self._io,), data)
#        data = self.presentation.sendMsg(data)
#        self._io.send(Packet(data))
        
    def start(self):
        """ Starts the client : connection to the server, etc. """
        # Try to connect to server
        if self.verbose: log.info("[HAPPYBOOM] Trying to connect to server %s:%u" % (self.host, self.port))
        self._io.on_connect = self.onConnect
        self._io.on_connection_fails = self.onConnectionFails
        self._io.on_disconnect = self.onDisconnect
        self._io.on_new_packet = self.presentation.processPacket
        self._io.on_lost_connection = self.onLostConnection
        self._io.connect(self.host, self.port)
        if not self._io.is_ready: return
        thread.start_new_thread(self._io.run_thread, ())
        
    def stop(self):
        """ Stops the display client : disconnection from the server, etc. """
        # Does not stop several times
        self.__stoplock.acquire()
        if self.__stopped:
            self.__stoplock.release()
            return False
        self.__stopped = True
        self.__stoplock.release()
        
        self._io.stop()
        if self.verbose:
            log.info("[HAPPYBOOM] Stopped")
        return True
        
    def __isStopped(self):
        self.__stoplock.acquire()
        stop = self.__stopped
        self.__stoplock.release()
        return stop
    stopped = property(__isStopped)
    
    def onConnect(self):
        """ Handler called on network connection. """
        if self.verbose:
            log.info("[HAPPYBOOM] Connected to server, send presentation connection().")
        self.launchEvent("happyboom", "connection", self._io, self.presentation.protocol.version.encode("ascii"), "")
        
    def onConnectionFails(self):
        """ Handler called when network connection fails. """
        log.error("[HAPPYBOOM] Fail to connect to the server.")

    def onDisconnect(self):
        """ Handler called on network disconnection. """
        if self.stopped: return
        log.info("[HAPPYBOOM] Connection to server closed")
        self.launchEvent("happyboom", "stop")

    def onLostConnection(self):
        """ Handler called on losting network connection. """
        log.warning("[HAPPYBOOM] Lost connection with server.")
        self.launchEvent("happyboom", "stop")
        
    def processPacket(self, new_packet):
        """ Processes incomming network packets (converts and launches local event).
        @param new_packet: incomming network packet.
        @type new_packet: C{net.io.packet.Packet}
        """
        event_type, arg = self.str2evt(new_packet.data)
        if event_type != None: 
            if self.debug:
                log.info("Received message: type=%s arg=%s" %(event_type, arg))
            self.launchEvent(event_type, arg)
            
class Gateway(EventLauncher, EventListener):
    def __init__(self, protocol, args):
        EventLauncher.__init__(self)
        EventListener.__init__(self, "evt_")
        self.protocol = protocol
        self.launchEvent("happyboom", "register", "connection", self.processConnection)
        self.launchEvent("happyboom", "register", "disconnection", self.processDisconnection)
        self.launchEvent("happyboom", "register", "create_item", self.processCreate)
#        self.launchEvent("happyboom", "register", "destroy_item", self.processXX)
        self.launchEvent("happyboom", "register", "recv_event", self.processEvent)
        self.registerEvent("happyboom")
        self.verbose = args.get("verbose", False)
        self.debug = args.get("debug", False)
        self.features = []
        self.items = {}
        #self.gamepath = None
        self.module = __import__("client/items")
        
    def processConnection(self, ioclient, version, signature):
        self.launchEvent("happyboom", "signature", ioclient, signature)
        features = ""
        for name in self.features:
            try:
                feature = self.protocol.getFeature(name)
                features = features + "%c" % feature.id
            except ProtocolException:
                pass
        self.launchEvent("happyboom", "features", ioclient, features)
        
    def processDisconnection(self, reason):
        self.launchEvent("happyboom", "stop", reason)
    
    def processCreateItem(self, feature, id):
        assert feature in self.features, "Unexpected feature"
        classname = self.getClassnameByFeature(feature)
        assert hasattr(self.module, classname), "Item class not found : %s" %classname
        itemclass = getattr(self.module, classname)
        item = itemclass(id)
        self.items[id] = item
        self.launchEvent(feature, "new", id)
    
    def processDestroyItem(self, id):
        assert id in self.items, "Unknown item identifier %s" %id
        self.launchEvent(feature, "delete", id)
        del self.items[id]
        
    def processEvent(self, ioclient, feature, event, *args):
        self.launchEvent(feature, event, *args)

    def getClassnameByFeature(self, feature):
        classname = ""
        prefix = True
        space = True
        for i in range(len(feature)):
            if feature[i] not in string.ascii_letters:
                if prefix:
                    classname = classname + feature[i]
                space = True
            else:
                prefix = False
                if space:
                    classname = classname + feature[i].upper()
                else:
                    classname = classname + feature[i]
        return classname

#    def evt_happyboom_gamepath(self, path):
#        self.gamepath = path
        
    def processCreate(self, ioclient, type, id):
        try:
            type = self.protocol.getFeatureById(type)
            type = type.name
        except ProtocolException, err:
            log.error(err)
            return
        self.launchEvent("happyboom", "doCreateItem", type, id)

    def processEvent(self, ioclient, feature, event, *args):       
        if self.debug:
            log.info("New event: %s.%s%s" % (feature, event, args))
        self.launchEvent(feature, event, *args)
