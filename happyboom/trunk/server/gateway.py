from happyboom.server.agent import Agent, Message
from happyboom.common.protocol import loadProtocol, ProtocolException
from happyboom.net.io import Packet
from happyboom.common.log import log
from pysma import Kernel, DummyScheduler
import struct

class Gateway(Agent):
    def __init__(self, protocol, presentation, client_manager, arg):
        Agent.__init__(self, self, "gateway")
        self.__protocol = protocol
        self.client_manager = client_manager
        self.presentation = presentation
        self.presentation.gateway = self 
        self.presentation.client_manager = self.client_manager
        self.client_manager.presentation = self.presentation
        self.__server = None 
        self._debug = arg.get("debug", False)
        self._verbose = arg.get("verbose", False)
        self.__scheduler = DummyScheduler(sleep=0.01)
        Kernel().addAgent(self.__scheduler)

    def __setServer(self, server):
        self.__server = server
        self.client_manager.server = server
    server = property(None, __setServer)

    # Create a network packet for the event feature.event(args)
    def createMsg(self, feature, event, *args):
        data = self.__protocol.createMsg(feature, event, *args)
        data = self.presentation.sendMsg(data)
        return Packet(data)
            
    def start(self):
        self.client_manager.start()
        Kernel.instance.addAgent(self)
        
    def stop(self):
        self.sendNetMsg("game", "stop")
        self.client_manager.stop()
        Kernel.instance.stopKernel()

    def process(self):
        # Stop server if the scheduler is dead
        if not self.__scheduler.alive:
            self.__server.stop()
        self.client_manager.process()

    def sendText(self, txt, client=None):
        if client != None:
            client.sendMsg("chat", "message", txt)
        else:
            self.sendNetMsg("chat", "message", txt)

    def recvNetMsg(self, feature, event, *args):
        message = Message("%s_%s" % (feature, event), args)
        self.sendBroadcastMessage(message, "%s_listener" % feature)

    def sendNetMsg(self, feature, event, *args):
        try:
            packet = self.createMsg(feature, event, *args)
        except ProtocolException, err:
            log.error(err)
            return
        clients = self.client_manager.supported_features.get(feature, ())
        for client in clients:
            client.sendPacket(packet)

    def __getProtocolVersion(self): return self.__protocol.version
    protocol_version = property(__getProtocolVersion)


