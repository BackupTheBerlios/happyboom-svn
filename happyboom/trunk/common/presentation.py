from happyboom.common.packer import packUtf8, packBin
from happyboom.common.simple_event import EventLauncher, EventListener
from happyboom.common.log import log
from happyboom.common.packer import unpack, unpackBin, unpackUtf8
from happyboom.net.io.packet import Packet
from happyboom.server.client import Client
import struct

class PresentationException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class Presentation(EventLauncher, EventListener):
    
    CONNECTION    = 0x1
    DISCONNECTION = 0x2
    FEATURES      = 0x3
    CREATE        = 0x4
    DESTROY       = 0x5
    EVENT         = 0x6
    
    def __init__(self, protocol, is_server):
        EventListener.__init__(self)
        EventLauncher.__init__(self)
        self.protocol = protocol
        self.items = {}
        self.gateway = None
        self.client_manager = None
        self.is_server = is_server 
        
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
        if ptype == self.CONNECTION:
            data = self.recvConnection(packet.recv_from, data)
        elif ptype == self.DISCONNECTION:
            data = self.processDisconnect(packet.recv_from, data)
        elif ptype == self.FEATURES:
            data = self.processFeatures(packet.recv_from, data)
        elif ptype == self.CREATE:
            data = self.createItem(data)
        elif ptype == self.DESTROY:
            data = self.destroyItem(data)
        elif ptype == self.EVENT:
            data = self.processEvent(data)
        else:
            log.warning("ProtocoleWarning: received unexpected packet type %s." % ptype)
        if len(data) != 0:
            log.warning("ProtocolWarning: Received a message with an unexpected length.")
            log.warning(u"Rest: [%s]." % data)

    def processDisconnect(self, ioclient, data):
        reason, data = unpackUtf8(data)
        if self.is_server:
            self.client_manager.closeClient(ioclient)
        else:
            log.warning(u"Received disconnected from server: %s" % reason)
            self.launchEvent("happyboom", "stop")
        return data
        
    def processFeatures(self, ioclient, data):
        features, data = unpackBin(data)
        print "Features: %s" % (features)
        client = Client(ioclient, self.gateway, self.client_manager)
        self.client_manager.appendClient(client)
        return data

    def recvConnection(self, client, data):
        version, data = unpackBin(data)
        signature, data = unpackBin(data) 
        
        if version != self.protocol.version:
            # TODO: send presentation bye(<why>)
            raise PresentationException("Wrong protocol version.")
        else:
            if self.is_server:
                # Send hello().
                self.client_manager.generateSignature(client)
                packet = self.connectionPacket(signature)
            else:
                # Send features().
                self.launchEvent("signature", (signature,))
                packet = self.featuresPacket()
            client.send(packet)
        return data
            
    def featuresPacket(self, features="TODO: Feed me!"):
        data = struct.pack("!B", self.FEATURES)
        data = data + packBin(features)
        return Packet(data)
       
    def createItem(self, data):
        # TODO
        return data

    def connectionPacket(self, signature=""):
        data = struct.pack("!B", self.CONNECTION)
        data = data + packBin(self.protocol.version.encode("ascii"))
        data = data + packBin(signature)
        return Packet(data)

    def disconnectionPacket(self, reason):
        data = struct.pack("!B", self.DISCONNECTION) + packUtf8(reason)
        return Packet(data)

    def sendMsg(self, data):
        data = struct.pack("!B", self.EVENT) + data
        return data
        
    def destroyItem(self, data):
        # TODO
        return data
    
    def processEvent(self, data):
        fmt = "!BB"
        i = struct.calcsize(fmt)
        feature_id, event_id = struct.unpack(fmt, data[:i])
        data = data[i:]

        feature, event, args = unpack(data, feature_id, event_id, self.protocol)
        log.info("Received: %s.%s(%s)" \
            % (feature, event, args))

        self.gateway.recvNetMsg(feature, event, args)
        return ""
