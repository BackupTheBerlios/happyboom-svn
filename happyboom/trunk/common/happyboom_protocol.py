from presentation import Presentation
from happyboom.common.packer import unpack, unpackBin, unpackUtf8, unpackInt
import struct

class HappyboomProtocol(Presentation):
    def __init__(self, protocol):
        Presentation.__init__(self, protocol)
        self._unpackFunc = { \
            self.CONNECTION: self.unpackConnection,
            self.DISCONNECTION: self.unpackDisconnect,
            self.FEATURES: self.unpackFeatures,
            self.CREATE: self.unpackCreateItem,
            self.DESTROY: self.unpackDestroyItem,
            self.EVENT: self.unpackEvent}

    def unpackPacketType(self, data):
        # Get packet type
        fmt = "!B"
        i = struct.calcsize(fmt)
        type, = struct.unpack(fmt, data[:i]) 
        return type, data[i:]

    def unpackDisconnect(self, ioclient, data):
        reason, data = unpackUtf8(data)
        if self._on_disconnection != None:
            self._on_disconnection(ioclient, reason)
#            self.client_manager.closeClient(ioclient)
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
        log.info("Received: %s.%s(%s)" % (feature, event, args))

        if self._on_recv_event != None:
            self._on_recv_event(ioclient, feature, event, args)
        return ""

    def unpackConnection(self, ioclient, data):
        version, data = unpackBin(data)
        signature, data = unpackBin(data) 
        if self._on_connection != None:
            self._on_connection(ioclient, version, signature)
        return data
