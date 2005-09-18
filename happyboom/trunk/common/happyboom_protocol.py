from presentation import Presentation
import happyboom.common.packer as packer
from happyboom.common.log import log
import struct

class HappyboomProtocol(Presentation):
    def __init__(self, protocol, args):
        Presentation.__init__(self, protocol, args)
        self._unpackFunc = { \
            self.CONNECTION: self.unpackConnection,
            self.DISCONNECTION: self.unpackDisconnection,
            self.FEATURES: self.unpackFeatures,
            self.CREATE: self.unpackCreateItem,
            self.DESTROY: self.unpackDestroyItem,
            self.EVENT: self.unpackEvent}

    def packConnection(self, version, signature):
        data = struct.pack("!B", self.CONNECTION)
        data = data + packer.packBin(version)
        return data + packer.packBin(signature)

    def packDisconnection(self, reason):
        return struct.pack("!B", self.DISCONNECTION) + packer.packUtf8(reason)

    def packFeatures(self, features):
        data = struct.pack("!B", self.FEATURES)
        return data + packer.packBin(features)

    def packCreate(self, feature, id):
        return struct.pack("!BBI", self.CREATE, feature, id)

    def packEvent(self, id):
        return struct.pack("!BI", self.DESTROY, id)

    def packEvent(self, feature, event, args):
        f = self.protocol.getFeature(feature)
        e = f.getEvent(event)
        out = struct.pack("!BB", f.id, e.id)
        types = e.getParamTypes()
        if len(args) != len(types):
            raise ProtocolException( \
                "Unexpected number of parameters (%u) for the event %s.%s." \
                % (len(args), f.name, e))
        for i in range(len(args)):
            if not packer.checkType(types[i], args[i]):
                raise ProtocolException( \
                    "Parameter %u of event %s.%s should have type %s (instead of %s)." \
                    % (i, f.name, e, types[i], type(args[i])))
            type = types[i]
            data = args[i]
            
            if type=="int":
                data = packer.packInt(data)
            elif type=="bin":
                data = packer.packBin(data)
            elif type=="utf8":
                data = packer.packUtf8(data)
            else:
                raise packer.PackerException("Wrong argument type: %s" % type)
            out = out + data
        return struct.pack("!B", self.EVENT) + out

    def unpackPacketType(self, data):
        # Get packet type
        fmt = "!B"
        i = struct.calcsize(fmt)
        type, = struct.unpack(fmt, data[:i]) 
        return type, data[i:]

    def unpackConnection(self, ioclient, data):
        version, data = packer.unpackBin(data)
        signature, data = packer.unpackBin(data) 
        if self._on_connection != None:
            self._on_connection(ioclient, version, signature)
        return data

    def unpackDisconnection(self, ioclient, data):
        reason, data = packer.unpackUtf8(data)
        if self._on_disconnection != None:
            self._on_disconnection(ioclient, reason)
#            self.client_manager.closeClient(ioclient)
        return data
        
    def unpackFeatures(self, ioclient, data):
        features, data = packer.unpackBin(data)
        if self._on_features != None:
            self._on_features(ioclient, features)
        return data

    def unpackCreateItem(self, ioclient, data):
        fmt = "!BI"
        i = struct.calcsize(fmt)
        typeid, itemid = struct.unpack(fmt, data)
        type = self.protocol[typeid]
        data = data[i:]
        if self._on_create_item != None:
            self._on_create_item(ioclient, type.name, itemid)
        return data

    def unpackDestroyItem(self, ioclient, data):
        itemid,data = packer.unpackInt(data)
        if self._on_destroy_item != None:
            self._on_destroy_item(ioclient, itemid)
        return data
    
    def unpackEvent(self, ioclient, data):
        fmt = "!BB"
        i = struct.calcsize(fmt)
        feature_id, event_id = struct.unpack(fmt, data[:i])
        feat = self.protocol[feature_id]
        evt = feat[event_id]
        data = data[i:]
        args = []
        for type in evt.getParamTypes():
            if type=="int":
                arg, data = packer.unpackInt(data)
            elif type=="bin":
                arg, data = packer.unpackBin(data)
            elif type=="utf8":
                arg, data = packer.unpackUtf8(data)
            else:
                raise packer.PackerException("Wrong argument type: %s" % type)
            args.append(arg)
        if self._on_recv_event != None:
            self._on_recv_event(ioclient, feat.name, evt.name, tuple(args))
        return ""
