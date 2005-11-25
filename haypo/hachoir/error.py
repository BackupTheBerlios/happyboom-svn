import os
import pygtk
pygtk.require ('2.0') # 2.2 for Clipboard
import gtk
from log import log
import ui.ui as ui

def warning(message):
    log.warning(message)
    if ui.ui != None:
        dlg = gtk.MessageDialog( \
            type=gtk.MESSAGE_WARNING,
            buttons=gtk.BUTTONS_OK,
            message_format=message)
        dlg.run()
        dlg.destroy()

def error(message):
    log.error(message)
    if ui.ui != None:
        dlg = gtk.MessageDialog( \
            type=gtk.MESSAGE_ERROR,
            buttons=gtk.BUTTONS_OK,
            message_format=message)
        dlg.run()
        dlg.destroy()
