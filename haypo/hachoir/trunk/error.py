import os
import config
from log import log
import ui.ui
from tools import getBacktrace

def warning(message):
    log_message = message + "\n\n" + getBacktrace()
    if config.debug:
        message = log_message
    log.warning(log_message)   
    if ui.ui.ui != None:
        import gtk
        dlg = gtk.MessageDialog( \
            parent=ui.ui.ui.window.window,
            type=gtk.MESSAGE_WARNING,
            buttons=gtk.BUTTONS_OK,
            message_format=message)
        dlg.run()
        dlg.destroy()

def error(message, backtrace=None):
    log_message = message + "\n\n" + getBacktrace()
    if config.debug:
        message = log_message
    log.error(log_message)
    if ui.ui.ui != None:
        import gtk
        dlg = gtk.MessageDialog( \
            parent=ui.ui.ui.window.window,
            type=gtk.MESSAGE_ERROR,
            buttons=gtk.BUTTONS_OK,
            message_format=message)
        dlg.run()
        dlg.destroy()
