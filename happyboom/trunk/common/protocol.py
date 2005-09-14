"""
Tools to load HappyBoom protocol in Python from an XML description file.
"""

import xml.dom.minidom
from happyboom.common.packer import pack, checkType

class ProtocolException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class ProtocolEventParam:
    def __init__(self, event, name, type):
        self.name = name
        self.type = type
        self.event = event

    def __str__(self):
        return "%s: %s" % (self.name, self.type)
       
class ProtocolEvent:
    def __init__(self, feature, name, id):
        self.name = name
        self.id = id
        self.feature = feature
        self.__params_dict = {}
        self.__params_array = [] 
        
    def addParam(self, name, id):
        param = ProtocolEventParam(self, name, id)
        self.__params_dict[name] = param
        self.__params_array.append(param)
        return param

    def getParamTypes(self):
        types = []
        for param in self.__params_array:
            types.append(param.type)
        return types
        
    def __str__(self):
        out = "%s(" % (self.name)
        comma = False
        for param in self.__params_array:
            if comma:
                out = out + ","
            else:
                comma = True
            out = out + str(param)
        out = out + ")"
        return out

class ProtocolFeature:
    def __init__(self, protocol, name, id):
        self.protocol = protocol
        self.name = name
        self.id = id
        self.__evtnames = {}
        self.__evtids = {}

    def addEvent(self, name, id):
        # Check if no other event have the same identifier
        event = self.__evtids.get(id, None)
        if event != None:
            raise ProtocolException( \
                "Events %s.%s and %s.%s have the same identifier (%s)." \
                % (self.name, event.name, self.name, name, id))
        # Check if no other event have the same name
        event = self.__evtnames.get(name, None)
        if event != None:
            raise ProtocolException( \
                "Events %s[%s] and %s[%s] have the same name (%s)." \
                % (self.name, event.id, self.name, id, name))

        # Add the new event 
        event = ProtocolEvent(self, name, id)
        self.__evtnames[name] = event
        self.__evtids[id] = event
        return event

    def getEvent(self, name):
        event = self.__evtnames.get(name, None)
        if event == None:
            raise ProtocolException( \
                "The protocol %s has no event %s.%s(...)." 
                % (self.protocol.name, self.name, name))
        return self.__evtnames[name]

    def getEventById(self, id):
        event = self.__evtids.get(id, None)
        if event == None:
            raise ProtocolException( \
                "The protocol %s has no event %s[%s](...)." 
                % (self.protocol.name, self.name, id))
        return self.__evtids[id]

    def __str__(self):
        first = True
        out = ""
        for event in self.__evtnames.values():
            if first:
                first = False
            else:
                out = out + "\n"
            out = out + "%s.%s" % (self.name, event)
        return out

class Protocol:
    """
    HappyBoom protocol utility.
    version is unicode
    """
    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.__featnames = {}
        self.__featids = {}

    def createMsg(self, feature, event, *args):
        f = self.getFeature(feature)
        e = f.getEvent(event)
        types = e.getParamTypes()
        if len(args) != len(types):
            raise ProtocolException( \
                "Wrong parameter count (%u) for the event %s." \
                % (len(args), e))
        for i in range(len(args)):
            if not checkType(types[i], args[i]):
                raise ProtocolException( \
                    "Parameter %u of event %s should be of type %s (and not %s)." \
                    % (i, f, types[i], type(args[i])))
        return pack(f.id, e.id, types, args)

    def addFeature(self, name, id):
        # Check if no other feature have the same identifier
        feature = self.__featnames.get(name, None)
        if feature != None:
            raise ProtocolException( \
                "Features %s and %s have the same identifier (%s)." \
                % (feature.name, name, id))
                
        # Check if no other feature have the same name
        feature = self.__featids.get(id, None)
        if feature != None:
            raise ProtocolException( \
                "Features %s and %s have the same name (%s)." \
                % (feature.id, id, name))

        # Add the new feature
        feature = ProtocolFeature(self, name, id)
        self.__featnames[name] = feature
        self.__featids[id] = feature
        return feature

    def getFeature(self, name):
        feature = self.__featnames.get(name, None)
        if feature == None:
            raise ProtocolException( \
                "The protocol %s has no feature \"%s\"." \
                % (self.name, name))
        return feature

    def getFeatureById(self, id):
        feature = self.__featids.get(id, None)
        if  feature == None:
            raise ProtocolException( \
                "The protocol %s has no feature with \"%s\" identifier." \
                % (self.name, id))
        return feature
        
    def __str__(self):
        out = ""
        first = True
        for feature in self.__featnames.values():
            if first:
                first = False
            else:
                out = out + "\n"
            out = out + "[ %s ]\n" % feature.name
            out = out + str(feature)
        return out
 
def loadProtocol(filename):
    doc = xml.dom.minidom.parse(filename)
    protocol = doc.documentElement
    p = Protocol( \
        protocol.getAttribute("name"),
        protocol.getAttribute("version"))
    features = protocol.getElementsByTagName("feature")
    for feature in features:
        f = p.addFeature( \
            feature.getAttribute("name"),
            int(feature.getAttribute("id")))
        events = feature.getElementsByTagName("event")
        for event in events:
            e = f.addEvent( \
                event.getAttribute("name"),
                int(event.getAttribute("id")))
            params = event.getElementsByTagName("param")
            for param in params:
                e.addParam( \
                    param.getAttribute("name"),
                    param.getAttribute("type"))
    return p
