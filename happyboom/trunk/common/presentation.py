from happyboom.common.event import EventListener
from happyboom.common.log import log
from happyboom.net.io.packet import Packet
from happyboom.server.client import Client
from happyboom.common.packer import packUtf8, packBin
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
    
    def __init__(self, protocol):
        EventListener.__init__(self, "evt_", silent=True)
        self.protocol = protocol
        self.items = {}
        self._unpackFunc = {}
        self.registerEvent("happyboom")

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
        @type ioclient L{IOClient}
        @type reason Unicode
        """
        self.evt_happyboom_disconnection(ioclient, reason)

    def evt_happyboom_features(self, ioclient, features):
        data = struct.pack("!B", self.FEATURES)
        data = data + packBin(features)
        ioclient.send( Packet(data) )
        
    def evt_happyboom_create(self, ioclient, feature, id):
        data = struct.pack("!BBI", self.CREATE, feature, id)
        ioclient.send( Packet(data) )
       
    def evt_happyboom_connection(self, ioclient, version, signature):
        """
        Send a connection message to ioclient.
        @type version ASCII string
        @type signature string
        """
       
        data = struct.pack("!B", self.CONNECTION)
        data = data + packBin(version)
        data = data + packBin(signature)
        ioclient.send( Packet(data) )

    def evt_happyboom_disconnection(self, ioclient, reason):
        """
        Send a disconnection message to ioclient.
        @type ioclient L{IOClient}
        @type reason Unicode
        """
        
        data = struct.pack("!B", self.DISCONNECTION) + packUtf8(reason)
        ioclient.send( Packet(data) )
        ioclient.disconnect()

    def evt_happyboom_event(self, clients, data):
        data = struct.pack("!B", self.EVENT) + data
        packet = Packet(data)
        for client in clients: client.send(packet)
        
    def unpackPacketType(self, data):
        """ returns type, data """
        return 0, data
    def unpackDisconnect(self, ioclient, data): return data
    def unpackFeatures(self, ioclient, data): return data
    def unpackCreateItem(self, data): return data
    def unpackDestroyItem(self, data): return data
    def unpackEvent(self, ioclient, data): return data
