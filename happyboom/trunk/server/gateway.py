from happyboom.server.agent import Agent, Message
from happyboom.common.protocol import loadProtocol, ProtocolException
from happyboom.net.io import Packet
from happyboom.common.log import log
from pysma import Kernel, DummyScheduler
from happyboom.common.simple_event import EventListener
import struct

class Gateway(Agent, EventListener):
    def __init__(self, protocol, presentation, client_manager, arg):
        EventListener.__init__(self)
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
        self.registerEvent("happyboom")
        Kernel().addAgent(self.__scheduler)

    def __setServer(self, server):
        self.__server = server
        self.client_manager.server = server
    server = property(None, __setServer)

    def evt_happyboom_network(self, feature, event, *args):
        self.sendMsg(feature, event, *args)
        
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

    def evt_happyboom_newClient(self, client):
        self.send("sync") #TODO: Add client argument ...

    def sendNetMsg(self, feature, event, *args):
        clients = self.client_manager.supported_features.get(feature, ())
        if len(clients)==0: return
        try:
            data = self.__protocol.createMsg(feature, event, *args)
        except ProtocolException, err:
            log.error(err)
            return
        self.launchEvent("happyboom", "event", clients, data);

    def __getProtocolVersion(self): return self.__protocol.version
    protocol_version = property(__getProtocolVersion)


