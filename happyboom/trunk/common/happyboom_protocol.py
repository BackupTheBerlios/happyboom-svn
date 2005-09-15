from presentation import Presentation
from happyboom.common.packer import unpack, unpackBin, unpackUtf8, unpackInt

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

    def unpackCreateItem(self, ioclient, data):
        itemid,data = unpackInt(data)
        type,data = unpackBin(data)
        if self._on_create_item != None:
            self._on_create_item(ioclient, type, itemid)
        return data

    def unpackDestroyItem(self, ioclient, data):
        itemid,data = unpackInt(data)
        if self._on_destroy_item != None:
            self._on_destroy_item(ioclient, itemid)
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
