from server.bb_agent import Agent
from happyboom.common.log import Log, log
import types

class LogAgent(Agent):
    def __init__(self, gateway, **args):
        Agent.__init__(self, "log", gateway, **args)
        self.registerEvent("gateway")
        log.on_new_message = self.onNewMessage

    def onNewMessage(self, level, prefix, text):
        if type(text) != types.UnicodeType:
            text = unicode(text)
        if level==Log.LOG_INFO:
            self.sendNetMsg("log", "info", text)
        elif level==Log.LOG_INFO:
            self.sendNetMsg("log", "warning", text)
        elif level==Log.LOG_INFO:
            self.sendNetMsg("log", "error", text)
        
    def evt_gateway_syncClient(self, client):
        # Send last messages?
        pass
