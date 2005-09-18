from happyboom.common.happyboom_protocol import HappyboomProtocol
from happyboom.common.protocol import ProtocolException
from happyboom.common.log import log
from happyboom.common.event import EventLauncher, EventListener
from happyboom.net.io.packet import Packet
from happyboom.net.io_tcp.tcp import IO_TCP
import struct, string, thread, imp, os.path, sys

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
        EventListener.__init__(self)
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
        
    def evt_happyboom_stop(self):
        self.stop()

    def evt_happyboom_network(self, feature, event, *args):
        self.launchEvent("happyboom", "event", (self._io,), feature, event, args)

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
        self.launchEvent("happyboom", "connection", self._io)
        
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
        
class Gateway(EventLauncher, EventListener):
    def __init__(self, protocol, args):
        EventLauncher.__init__(self)
        EventListener.__init__(self, "evt_")
        self.protocol = protocol
        self.launchEvent("happyboom", "register", "connection", self.processConnection)
        self.launchEvent("happyboom", "register", "disconnection", self.processDisconnection)
        self.launchEvent("happyboom", "register", "create_item", self.processCreateItem)
        self.launchEvent("happyboom", "register", "destroy_item", self.processDestroyItem)
        self.launchEvent("happyboom", "register", "recv_event", self.processEvent)
        self.registerEvent("happyboom")
        self.verbose = args.get("verbose", False)
        self.debug = args.get("debug", False)
        self.features = {}
        for feat in args.get("features", ()):
            self.features[feat] = None
        self.items = {}
        itemPath = args["item_path"]
        dirs = itemPath.split(os.path.sep)
        if dirs[-1] == "":
            dirs = dirs[:-1]
        packagePath = None
        try:
            for d in dirs:
                #print "imp.find_module(%s, %s)" %(repr(modName), repr(modDir))
                f, fname, desc = imp.find_module(d, packagePath)
                self.module = imp.load_module(d, f, fname, desc)
                packagePath = self.module.__path__
        except:
            raise Exception("[HAPPYBOOM] Invalid item path : %s" %itemPath)
        import types
        for attr in self.module.__dict__:
            if type(self.module.__dict__[attr]) == types.ClassType:
                itemClass = self.module.__dict__[attr]
                if hasattr(itemClass, "feature"):
                    feat = getattr(itemClass, "feature")
                    if feat != None:
                        if feat in self.features:
                            raise Exception("[HAPPYBOOM] Duplicated feature %s in %s and %s classes" %(feat, itemClass.__name__, self.features[feat].__name__))
                        self.features[feat] = itemClass
                    print "FEATURE : %s !!!!!!!!!!!!!!!!!!!!!!!" %feat
        
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
        
    def processDisconnection(self, ioclient, reason):
        self.launchEvent("happyboom", "stop", reason)
    
    def processCreateItem(self, ioclient, feature, id):
        assert feature in self.features, "Unexpected feature : %s" %feature
        itemClass = self.features[feature]
        if itemClass != None:
            item = itemClass(id)
            self.items[id] = item
            self.launchEvent(feature, "new", id)
    
    def processDestroyItem(self, ioclient, id):
        assert id in self.items, "Unknown item identifier %s" %id
        self.launchEvent(feature, "delete", id)
        del self.items[id]
        
    def processEvent(self, ioclient, feature, event, args):
        if self.debug:
            log.info("New event: %s.%s%s" % (feature, event, args))
        assert feature in self.features, "Unexpected feature"
        self.launchEvent(feature, event, *args)

#    def evt_happyboom_gamepath(self, path):
#        self.gamepath = path