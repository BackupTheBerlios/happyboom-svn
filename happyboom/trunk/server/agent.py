from pysma import ActionAgent, ActionMessage
from happyboom.common.log import log

class Agent(ActionAgent):
    """
    SMA agent in HappyBoom.
    """
    def __init__(self, type, gateway, **args):
        ActionAgent.__init__(self, prefix="msg_")
        self._gateway = gateway
        self.type = type
        self.__debug = args.get("debug", False)
        self.sendBroadcast = self.sendBroadcastMessage

    def born(self):
        self.requestRole(self.type)

    def requestActions(self, type):
        self.requestRole("%s_listener" %type)
        
    def send(self, action, *arg, **kw):
        message = Message("%s_%s" %(self.type, action), arg, kw)
        self.sendBroadcastMessage(message, "%s_listener" %self.type)

    def sendNetMsg(self, func, event, *args):
        self._gateway.sendNetMsg(func, event, *args)

    def messageReceived(self, msg):
        if self.__debug:
            log.warning("Unhandled message : %s -- %s" %(type(self), msg))

class Message(ActionMessage):
    def __init__(self, action, arg, kw={}):
        ActionMessage.__init__(self, action, arg, kw)
