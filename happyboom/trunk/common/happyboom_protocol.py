from presentation import Presentation
from packer import *


class HappyboomProtocol(Presentation):
    def unpackPacketType(self, data):
        # Get packet type
        fmt = "!B"
        i = struct.calcsize(fmt)
        ptype, = struct.unpack(fmt, data[:i]) 
        return data[i:]

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

    def unpackCreateItem(self, data):
        # TODO
        return data

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
