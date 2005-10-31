import pygtk
pygtk.require ('2.0')
import gtk
import gtk.glade
from chunk import FormatChunk
from ui_new_chunk import NewChunkDialog

class TablePopup:
    def __init__(self, ui, filename):
        self.ui = ui
        xml = gtk.glade.XML(filename, "table_popup")
        self.popup = xml.get_widget('table_popup')
        xml.signal_autoconnect(self)
        self.chunk = None
        self.new_chunk = NewChunkDialog(self.ui.glade_xml)

    def show(self, path_info, event):
        col = path_info[0][0]
        self.chunk = self.ui.getTableChunk(col)
        if self.chunk == None:
            print "Can't get chunk"
            return
        self.popup.popup( None, None, None, event.button, event.time)

    def onNewChunk(self, event):
        if self.new_chunk.runNewChunk() == gtk.RESPONSE_CANCEL: return
        assert issubclass(self.chunk.__class__, FormatChunk) and self.chunk.isString()
        format = self.new_chunk.getFormat()
        self.chunk.setFormat(format, "split")

    def onSetFormat(self, event):
        if issubclass(self.chunk.__class__, FormatChunk):
            if self.new_chunk.runSetFormat(self.chunk) == gtk.RESPONSE_CANCEL: return
            format = self.new_chunk.getFormat()
            self.chunk.setFormat(format, "rescan")
        else:
            print "Can't set format of chunk of type %s" % self.chunk.__class__

    def onJoinChunks(self, event):
        print "join chunk"
