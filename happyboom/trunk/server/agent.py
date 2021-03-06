from pysma import ActionAgent, ActionMessage as Message
from happyboom.common.log import log
from happyboom.common.event import EventLauncher, EventListener

class Agent(ActionAgent, EventLauncher, EventListener):
    """
    SMA agent in HappyBoom.
    """
    def __init__(self, type, gateway, **args):
        EventLauncher.__init__(self)
        EventListener.__init__(self)
        ActionAgent.__init__(self, prefix="msg_")
        self._gateway = gateway
        self.type = type
        self.__debug = args.get("debug", False)
        self.sendBroadcast = self.sendBroadcastMessage

    def netCreateItem(self, client):
        if self.type in client.features:
            self.launchEvent("happyboom", "netCreateItem", client, self)
        elif self.__debug:
            log.info("Client %s doesn't want item %s" % (client, self.type))

    def born(self):
        self.requestRole(self.type)

    def requestActions(self, type):
        self.requestRole("%s_listener" %type)
        
    def send(self, action, *arg, **kw):
        message = Message("%s_%s" %(self.type, action), arg, kw)
        self.sendBroadcastMessage(message, "%s_listener" %self.type)

    def sendNetMsg(self, func, event, *args):
        self.launchEvent("happyboom", "network", func, event, *args)

    def messageReceived(self, msg):
        if self.__debug:
            log.warning("Unhandled message : %s -- %s" %(type(self), msg))
