import xml.dom.minidom

class ProtocolEventParam:
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def __str__(self):
        return self.name
       
class ProtocolEvent:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.__params_dict = {}
        self.__params_array = [] 
        
    def addParam(self, name, id):
        param = ProtocolEventParam(name, id)
        self.__params_dict[name] = param
        self.__params_array.append(param)
        return param
        
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

class ProtocolFunc:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.__events = {}

    def addEvent(self, name, id):
        event = ProtocolEvent(name, id)
        self.__events[name] = event
        return event

    def __str__(self):
        first = True
        out = ""
        for event_name, event in self.__events.items():
            if first:
                first = False
            else:
                out = out + "\n"
            out = out + "%s.%s" % (self.name, event)
        return out

class Protocol:
    def __init__(self, version):
        self.__funcs = {}
        self.version = version

    def addFunc(self, name, id):
        func = ProtocolFunc(name, id)
        self.__funcs[name] = func
        return func

    def __str__(self):
        out = ""
        first = True
        for func_name, func in self.__funcs.items():
            if first:
                first = False
            else:
                out = out + "\n"
            out = out + "[ %s ]\n" % func.name
            out = out + str(func)
        return out
 
def loadProtocol(filename):
    doc = xml.dom.minidom.parse(filename)
    protocol = doc.documentElement
    p = Protocol(protocol.getAttribute("version"))
    funcs = protocol.getElementsByTagName("func")
    for func in funcs:
        f = p.addFunc( \
            func.getAttribute("name"),
            func.getAttribute("id"))
        events = func.getElementsByTagName("event")
        for event in events:
            e = f.addEvent( \
                event.getAttribute("name"),
                event.getAttribute("id"))
            params = func.getElementsByTagName("param")
            for param in params:
                e.addParam( \
                    param.getAttribute("name"),
                    param.getAttribute("id"))
    print "-- Protocol --"                
    print p
    print "-- Protocol end --"                
    return p
