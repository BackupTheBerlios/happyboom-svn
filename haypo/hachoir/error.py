import os
import pygtk
pygtk.require ('2.0')
import gtk
from log import log
import ui

def error(message):
    log.error(message)
    if ui.ui != None:
        dlg = gtk.MessageDialog( \
            type=gtk.MESSAGE_ERROR,
            buttons=gtk.BUTTONS_OK,
            message_format=message)
        dlg.run()
        dlg.destroy()