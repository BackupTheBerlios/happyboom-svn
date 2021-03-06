from happyboom.server.agent import Agent, Message
from happyboom.common.protocol import loadProtocol, ProtocolException
from happyboom.net.io import Packet
from happyboom.common.log import log
from pysma import Kernel, DummyScheduler
from happyboom.common.event import EventListener
import struct

class Gateway(Agent, EventListener):
    def __init__(self, protocol, presentation, client_manager, arg):
        EventListener.__init__(self, "evt_")
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

    def eventPerformed(self, event):
        p = self.pattern % self.getEventName(event.type, event.event)

    def __setServer(self, server):
        self.__server = server
        self.client_manager.server = server
    server = property(None, __setServer)

#    def eventPerformed(self, event):
#        print "gzzz", event

    def evt_happyboom_network(self, feature, event, *args):
        self.sendNetMsg(feature, event, *args)
        
    def evt_happyboom_netCreateItem(self, client, item):
        try:
            type = item.type
            type = self.presentation.protocol.getFeature(type)
            type = type.id
        except ProtocolException, err:
            log.error(err)
            return
        self.launchEvent("happyboom", "create", client.io, type, item.id);
        
    def start(self):
        Kernel.instance.addAgent(self)
        self.launchEvent("happyboom", "register", "recv_event", self.recvNetMsg)
        
    def stop(self):
        self.sendNetMsg("game", "stop")
        Kernel.instance.stopKernel()

    def process(self):
        # Stop server if the scheduler is dead
#       TODO: Waiting for last PySMA version...        
#        if not self.__scheduler.alive:
#            self.__server.stop()
        pass

    def sendText(self, txt, client=None):
        if client != None:
            client.sendMsg("chat", "message", txt)
        else:
            self.sendNetMsg("chat", "message", txt)

    def recvNetMsg(self, ioclient, feature, event, args):
        if self._verbose: log.info("Received: %s.%s%s" % (feature, event, args))
        message = Message("%s_%s" % (feature, event), args)
        self.sendBroadcastMessage(message, "%s_listener" % feature)

    def evt_happyboom_newClient(self, client):
        self.launchEvent("gateway", "syncClientCreate", client)
        self.launchEvent("gateway", "syncClient", client)

    def sendNetMsg(self, feature, event, *args):
        clients = self.client_manager.supported_features.get(feature, ())
        if len(clients)==0: return
        self.launchEvent("happyboom", "event", clients, feature, event, args);
