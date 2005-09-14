from happyboom.common import packer
from happyboom.server.agent import Agent
from pysma import Kernel, DummyScheduler
from happyboom.common.protocol import loadProtocol
from happyboom.net.io import Packet

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


    # Create a network packet for the event func.event(args) where
    # args is a tuple
    def createMsgTuple(self, func, event, args):
        data = packer.pack(func, event, args)
        return Packet(data)
            
    # Create a network packet for the event func.event(args), see
    # L{self.createMsgTuple}
    def createMsg(self, func, event, *args):
        return self.createMsgTuple(func, event, args)

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

    def sendNetMsg(self, func, event, *args):
        packet = self.createMsgTuple(func, type, args)
        clients = self.__client_manager.supported_features.get(func, ())
        for client in clients:
            client.sendPacket(packet)

    def __getProtocolVersion(self): return self.__protocol.version
    protocol_version = property(__getProtocolVersion)


