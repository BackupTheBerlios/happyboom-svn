from client.bb_item import BoomBoomItem

class LogItem(BoomBoomItem):
    def __init__(self):
        BoomBoomItem.__init__(self)
        self.registerEvent("log")
        
    def evt_log_info(self, text):
        log.info(u"[Server Log][info] %s" % text)
        
    def evt_log_warning(self, text):
        log.info(u"[Server Log][warn] %s" % text)
        
    def evt_log_error(self, text):
        log.info(u"[Server Log][err!] %s" % text)
