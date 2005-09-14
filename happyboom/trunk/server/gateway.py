from happyboom.common import packer 
from happyboom.server.agent import Agent
from pysma import Kernel, DummyScheduler
from happyboom.common.protocol import loadProtocol, ProtocolException
from happyboom.net.io import Packet
import struct

class Gateway(Agent):
    def __init__(self, protocol, client_manager, arg):
        Agent.__init__(self, self, "gateway")
        self.__protocol = protocol
        self.__client_manager = client_manager
        self.__server = None 
        self._debug = arg.get("debug", False)
        self._verbose = arg.get("verbose", False)
        self.__scheduler = DummyScheduler(sleep=0.01)
        Kernel().addAgent(self.__scheduler)

    def __setServer(self, server):
        self.__server = server
        self.__client_manager.server = server
    server = property(None, __setServer)


    # Create a network packet for the event feature.event(args)
    def createMsg(self, feature, event, *args):
        f = self.__protocol.getFeature(feature)
        e = f.getEvent(event)
        types = e.getParamsType()
        if len(args) != len(types):
            raise ProtocolException( \
                "Wrong parameter count (%u) for the event %s." \
                % (len(args), e))
        for i in range(len(args)):
            if not packer.checkType(types[i], args[i]):
                raise ProtocolException( \
                    "Parameter %u of event %s should be of type %s (and not %s)." \
                    % (i, event, types[i], type(args[i])))
        data = packer.pack(f.id, e.id, types, args)
        return Packet(data)
            
    def start(self):
        self.__client_manager.start()
        Kernel.instance.addAgent(self)
        
    def stop(self):
        self.sendNetMsg("game", "stop")
        self.__client_manager.stop()
        Kernel.instance.stopKernel()

    def process(self):
        # Stop server if the scheduler is dead
        if not self.__scheduler.alive:
            self.__server.stop()
        self.__client_manager.process()

    def sendText(self, txt, client=None):
        if client != None:
            client.sendMsg("agent_manager", "Text", txt)
        else:
            self.sendNetMsg("agent_manager", "Text", txt)

    def sendNetMsg(self, feature, event, *args):
        packet = self.createMsg(feature, event, *args)
        clients = self.__client_manager.supported_features.get(feature, ())
        for client in clients:
            client.sendPacket(packet)

    def __getProtocolVersion(self): return self.__protocol.version
    protocol_version = property(__getProtocolVersion)


