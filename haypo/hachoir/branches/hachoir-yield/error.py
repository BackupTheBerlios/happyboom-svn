import os
import config
from log import log
#import ui.ui
from tools import getBacktrace

def warning(message):
    if config.verbose or config.debug:
        message += "\n\n" + getBacktrace()
    log.warning(message)   
#    if (config.verbose or config.debug) and ui.ui.ui != None:
#        import gtk
#        dlg = gtk.MessageDialog( \
#            parent=ui.ui.ui.window.window,
#            type=gtk.MESSAGE_WARNING,
#            buttons=gtk.BUTTONS_OK,
#            message_format=message)
#        dlg.run()
#        dlg.destroy()

def error(message, backtrace=None):
    if config.verbose or config.debug:
        message += "\n\n" + getBacktrace()
    log.error(message)
#    if ui.ui.ui != None:
#        import gtk
#        dlg = gtk.MessageDialog( \
#            parent=ui.ui.ui.window.window,
#            type=gtk.MESSAGE_ERROR,
#            buttons=gtk.BUTTONS_OK,
#            message_format=message)
#        dlg.run()
#        dlg.destroy()
