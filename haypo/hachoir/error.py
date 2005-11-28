import os
from log import log
from ui.ui import ui as ui

def warning(message):
    log.warning(message)   
    if ui != None:
        dlg = gtk.MessageDialog( \
            type=gtk.MESSAGE_WARNING,
            buttons=gtk.BUTTONS_OK,
            message_format=message)
        dlg.run()
        dlg.destroy()

def error(message):
    log.error(message)
    if ui != None:
        dlg = gtk.MessageDialog( \
            type=gtk.MESSAGE_ERROR,
            buttons=gtk.BUTTONS_OK,
            message_format=message)
        dlg.run()
        dlg.destroy()
