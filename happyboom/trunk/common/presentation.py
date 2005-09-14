from happyboom.common.simple_event import EventLauncher, EventListener
from happyboom.common.log import log

class Presentation(EventLauncher, EventListener):
    
    CONNECTION    = 0x1
    DISCONNECTION = 0x2
    FEATURES      = 0x3
    CREATE        = 0x4
    DESTROY       = 0x5
    EVENT         = 0x6
    
    def __init__(self, protocol):
        self.protocol = protocol
        self.items = {}
        self.gateway = None
        
    def processPacket(self, newPacket):
        """ Processes incomming network packets (converts and launches local event).
        @param new_packet: incomming network packet.
        @type new_packet: C{net.io.packet.Packet}
        """
      
        # Get packet type
        data = new_packtet.data
        fmt = "!B"
        i = struct.calcsize(fmt)
        type, data = (struct.unpack(fmt, data[:i]), date[i:],)

        # Choose process function
        if type == self.CONNECTION:
            self.recvConnection(data)
            self.sendFeatures()
        elif type == self.DISCONNECTION:
            log.warning(u"Disconnected from server : %s" % self.getReason(data))
            self.launchEvent("happyboom", "stop")
        elif type == self.CREATE:
            self.createItem(data)
        elif type == self.DESTROY:
            self.destroyItem(data)
        elif type == self.EVENT:
            self.processEvent(data)
        else:
            log.warning("ProtocoleWarning: received unexpected packet type %s." % type)
        
    def recvConnection(self, data):
        fmt = "!H"
        i = struct.calcsize(fmt)
        version_len, data = (struct.unpack(fmt, data[:i]), data[i:])
        fmt = "!%us" %(version_len)
        i = struct.calcsize(fmt)
        version, data = (struct.unpack(fmt, data[:i]), data[i:])
        
        fmt = "!H"
        i = struct.calcsize(fmt)
        sign_len, data = (struct.unpack(fmt, data[:i]), data[i:])
        fmt = "!%us" %(version_len)
        i = struct.calcsize(fmt)
        signature, data = (struct.unpack(fmt, data[:i]), data[i:])
        
        if len(data) != 0:
            raise TesUneGrosseMerdeError "Received a message with an unexpected length."
        
        if version != protocole.version:
            pass # TODO
            
        self.launchEvent("happyboom", "signature", (signature,))
            
    def sendFeatures(self):
        pass
    
    def getReason(self, data):
        pass
    
    def createItem(self, data):
        pass

    def sendMsg(self, data):
        data = struct.pack("!B", self.EVENT) + data
        return data
        
    def destroyItem(self, data):
        pass
    
    def processEvent(self, data):
        packer.unpack(data, self.protocol)
        if self.__debug:
            log.info("Received message: feature=%s event=%s arguments=%s." % (feat, evt, args))
        self.launchEvent(feat, evt, args)
