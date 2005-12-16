import os
from log import log
import ui.ui

def warning(message):
    log.warning(message)   
    if ui.ui.ui != None:
        import gtk
        dlg = gtk.MessageDialog( \
            parent=ui.ui.ui.window,
            type=gtk.MESSAGE_WARNING,
            buttons=gtk.BUTTONS_OK,
            message_format=message)
        dlg.run()
        dlg.destroy()

def error(message):
    log.error(message)
    if ui.ui.ui != None:
        import gtk
        dlg = gtk.MessageDialog( \
            parent=ui.ui.ui.window,
            type=gtk.MESSAGE_ERROR,
            buttons=gtk.BUTTONS_OK,
            message_format=message)
        dlg.run()
        dlg.destroy()
