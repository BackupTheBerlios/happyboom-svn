from client.item import Item
from happyboom.common.log import log

class LogItem(Item):
    feature = "log"
    
    def __init__(self, id):
        Item.__init__(self, id)
        self.registerEvent("log")
        
    def evt_log_info(self, text):
        log.info(u"[Server Log][info] %s" % text)
        
    def evt_log_warning(self, text):
        log.info(u"[Server Log][warn] %s" % text)
        
    def evt_log_error(self, text):
        log.info(u"[Server Log][err!] %s" % text)
