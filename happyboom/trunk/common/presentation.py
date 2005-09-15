from happyboom.common.packer import packUtf8, packBin
from happyboom.common.simple_event import EventListener
from happyboom.common.log import log
from happyboom.common.packer import unpack, unpackBin, unpackUtf8
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
    
    def __init__(self, protocol, is_server):
        EventListener.__init__(self)
        self.protocol = protocol
        self.items = {}
        self.gateway = None
        self.is_server = is_server 
        self._unpackFunc = { \
            self.CONNECTION: self.unpackConnection,
            self.DISCONNECTION: self.unpackDisconnect,
            self.FEATURES: self.unpackFeatures,
            self.CREATE: self.unpackCreateItem,
            self.DESTROY: self.unpackDestroyItem,
            self.EVENT: self.unpackEvent}

        # Event (IOClient client, str version, str signature)
        self._on_client_connection = None

        # Event (IOClient client, str features)
        self._on_features = None
        
        # Event (IOClient client)
        self._on_client_disconnection = None

        # Event (IOClient client, str feature, str event, str arguments)
        self._on_recv_event = None

        # Event (IOClient client, str type, int id)
        self._on_create_item = None

        # Event (IOClient client, int id)
        self._on_destroy_item = None
        
    def processPacket(self, packet):
        """ Processes incomming network packets (converts and launches local event).
        @param packet: incomming network packet.
        @type packet: C{net.io.packet.Packet}
        """
      
        # Get packet type
        data = packet.data
        fmt = "!B"
        i = struct.calcsize(fmt)
        ptype, = struct.unpack(fmt, data[:i]) 
        data = data[i:]

        # Choose process function
        if ptype in self._unpackFunc:
            self._unpackFunc(packet.recv_from, data)
        else:
            log.warning("ProtocoleWarning: received unexpected packet type %s." % ptype)
        if len(data) != 0:
            log.warning("ProtocolWarning: Received a message with an unexpected length.")
            log.warning(u"Rest: [%s]." % data)

    def unpackDisconnect(self, ioclient, data):
        reason, data = unpackUtf8(data)
        if self.is_server:
            self.client_manager.closeClient(ioclient)
        else:
            log.warning(u"Received disconnected from server: %s" % reason)
            self.launchEvent("happyboom", "stop")
        return data
        
    def unpackFeatures(self, ioclient, data):
        features, data = unpackBin(data)
        if self._on_features != None:
            self._on_features(ioclient, features)
        return data

    def evt_happyboom_closeConnection(self, ioclient, reason):
        """
        Close client connection.
        @type ioclient L{IOClient}
        @type reason Unicode
        """
        self.evt_happyboom_clientDisconnection(ioclient, reason)

    def unpackConnection(self, ioclient, data):
        version, data = unpackBin(data)
        signature, data = unpackBin(data) 
        
        if self._on_client_connection != None:
            self._on_client_connection(ioclient, version, signature)
#        if version != self.protocol.version:
#            # TODO: send presentation bye(<why>)
#            raise PresentationException("Wrong protocol version.")
#        else:
#            if not self.is_server:
#                self.launchEvent("signature", (signature,))
#                packet = self.featuresPacket()
#                ioclient.send(packet)
        return data
            
    def featuresPacket(self, features="TODO: Feed me!"):
        data = struct.pack("!B", self.FEATURES)
        data = data + packBin(features)
        return Packet(data)
       
    def unpackCreateItem(self, data):
        # TODO
        return data

    def evt_happyboom_clientConnection(self, ioclient, version, signature=""):
        """
        Send a connection message to ioclient.
        @type version ASCII string
        @type signature string
        """
        
        data = struct.pack("!B", self.CONNECTION)
        data = data + packBin(version)
        data = data + packBin(signature)
        ioclient.send( Packet(data) )

    def evt_happyboom_clientDisconnection(self, ioclient, reason):
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
        
    def unpackDestroyItem(self, data):
        # TODO
        return data
    
    def unpackEvent(self, ioclient, data):
        fmt = "!BB"
        i = struct.calcsize(fmt)
        feature_id, event_id = struct.unpack(fmt, data[:i])
        data = data[i:]

        feature, event, args = unpack(data, feature_id, event_id, self.protocol)
        log.info("Received: %s.%s(%s)" \
            % (feature, event, args))

        self.gateway.recvNetMsg(feature, event, args)
        return ""
