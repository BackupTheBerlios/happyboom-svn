import xml.dom.minidom

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

    def getParamsType(self):
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
        self.__events = {}

    def addEvent(self, name, id):
        # Check if no other event have the same identifier
        for event in self.__events.values():
            if event.id==id:
                raise ProtocolException( \
                    "Events %s.%s and %s.%s have the same identifier (%s)." \
                    % (self.name, event.name, self.name, name, id))

        # Add the new event 
        event = ProtocolEvent(self, name, id)
        self.__events[name] = event
        return event

    def getEvent(self, event):
        if not self.__events.has_key(event):
            raise ProtocolException( \
                "The protocol %s has no event %s.%s(...)." 
                % (self.protocol.name, self.name, event))
        return self.__events[event]

    def __str__(self):
        first = True
        out = ""
        for event in self.__events.values():
            if first:
                first = False
            else:
                out = out + "\n"
            out = out + "%s.%s" % (self.name, event)
        return out

class Protocol:
    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.__features = {}

    def addFeature(self, name, id):
        # Check if no other feature have the same identifier
        for feature in self.__features.values():
            if feature.id==id:
                raise ProtocolException( \
                    "Features %s and %s have the same identifier (%s)." \
                    % (feature.name, name, id))

        # Add the new feature
        feature = ProtocolFeature(self, name, id)
        self.__features[name] = feature
        return feature

    def getFeature(self, feature):
        if not self.__features.has_key(feature):
            raise ProtocolException( \
                "The protocol %s has no feature %s." \
                % (self.name, feature))
        return self.__features[feature]

    def __str__(self):
        out = ""
        first = True
        for feature in self.__features.values():
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
