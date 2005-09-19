from happyboom.common.event import EventListener
from happyboom.common.log import log
from happyboom.net.io.packet import Packet
from happyboom.server.client import Client
import struct

class PresentationException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class Presentation(EventListener):
    
    CONNECTION    = 0x1
    DISCONNECTION = 0x2
    FEATURES      = 0x3
    CREATE        = 0x4
    DESTROY       = 0x5
    EVENT         = 0x6
    
    def __init__(self, protocol, args):
        EventListener.__init__(self)
        self.protocol = protocol
        self.items = {}
        self._unpackFunc = {}
        self.registerEvent("happyboom")
        self.verbose = args.get("verbose", False)

        # Event (IO_Client client, str version, str signature)
        self._on_connection = None
        # Event (IO_Client client, str features)
        self._on_features = None
        # Event (IO_Client client)
        self._on_disconnection = None
        # Event (IO_Client client, str feature, str event, str arguments)
        self._on_recv_event = None
        # Event (IO_Client client, str type, int id)
        self._on_create_item = None
        # Event (IO_Client client, int id)
        self._on_destroy_item = None

    def processPacket(self, packet):
        """ Processes incomming network packets (converts and launches local event).
        @param packet: incomming network packet.
        @type packet: C{net.io.packet.Packet}
        """
        ptype, data = self.unpackPacketType(packet.data)
        
        # Choose process function
        if ptype in self._unpackFunc:
            data = self._unpackFunc[ptype] (packet.recv_from, data)
        else:
            log.warning("ProtocoleWarning: received unexpected packet type %s." % ptype)
        if len(data) != 0:
            log.warning("ProtocolWarning: Received a message with an unexpected length.")
            log.warning(u"Rest: [%s]." % data)

    def evt_happyboom_register(self, event, handler):
        event = "_on_"+event
        if hasattr(self, event):
            setattr(self, event, handler)
    
    def evt_happyboom_closeConnection(self, ioclient, reason):
        """
        Close client connection.
        @type ioclient: L{IOClient}
        @type reason: C{unicode}
        """
        self.evt_happyboom_disconnection(ioclient, reason)

    def evt_happyboom_connection(self, ioclient, version=None, signature=""):
        """
        Send a connection message to ioclient.
        @type version: str
        @type signature: str
        """
        if version == None:
            version = self.protocol.version
        if self.verbose:
            log.info("[PRESENTATION] Send connection(\"%s\", \"%s\")" % (version, signature))
        data = self.packConnection(version, signature)
        ioclient.send( Packet(data) )

    def evt_happyboom_disconnection(self, ioclient, reason):
        """
        Send a disconnection message to ioclient.
        @type ioclient: L{IOClient}
        @type reason: unicode
        """
        
        if self.verbose:
            log.info(u"[PRESENTATION] Send disconnection(\"%s\")" % reason)
        data = self.packDisconnection(reason)
        ioclient.send( Packet(data) )
        ioclient.disconnect()
    

    def evt_happyboom_features(self, ioclient, features):
        if self.verbose:
            log.info(u"[PRESENTATION] Send features(%s)" % features)
        data = self.packFeatures(features)
        ioclient.send( Packet(data) )
        
    def evt_happyboom_create(self, ioclient, feature, id):
        if self.verbose:
            log.info(u"[PRESENTATION] Send create(%s, %s)" % (feature, id))
        data = self.packCreate(feature, id)
        ioclient.send( Packet(data) )
       
    
    def evt_happyboom_event(self, clients, feature, event, args):
        data = self.packEvent(feature, event, args)
        packet = Packet(data)
        for client in clients: client.send(packet)
        
    def unpackPacketType(self, data):
        """ returns type, data """
        return 0, data
        
    def unpackConnection(self, ioclient, version, signature): return data
    def unpackDisconnection(self, ioclient, data): return data
    def unpackFeatures(self, ioclient, data): return data
    def unpackCreateItem(self, data): return data
    def unpackDestroyItem(self, data): return data
    def unpackEvent(self, ioclient, data): return data

    def packConnection(self, version, signature): return ""
    def packDisconnect(self, reason): return ""
    def packFeatures(self, features): return ""
    def packCreateItem(self, feature, id): return ""
    def packDestroyItem(self, id): return ""
    def packEvent(self, feature, event, args): return ""
