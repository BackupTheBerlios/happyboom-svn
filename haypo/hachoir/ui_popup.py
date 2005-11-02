import pygtk
pygtk.require ('2.0')
import gtk
import gtk.glade
from chunk import FormatChunk, FilterChunk
from ui_new_chunk import NewChunkDialog
from format import splitFormat # TODO: remove this line
from error import error

class TablePopup:
    def __init__(self, ui, filename):
        self.ui = ui
        xml = gtk.glade.XML(filename, "table_popup")
        self.popup = xml.get_widget('table_popup')
        xml.signal_autoconnect(self)
        self.chunk = None
        self.new_chunk_dlg = NewChunkDialog(self.ui.glade_xml)

        # Popup items
        self.new_chunk = xml.get_widget("new_chunk")
        self.new_filter = xml.get_widget("new_filter")
        self.convert = xml.get_widget("convert")
        self.set_format = xml.get_widget("set_format")
        self.delete_chunk = xml.get_widget("delete_chunk")

    def show(self, path_info, event):
        col = path_info[0][0]
        self.chunk = self.ui.window.getTableChunk(col)
        if self.chunk == None:
            error("Can't get chunk")
            return

        is_format_chunk = issubclass(self.chunk.__class__, FormatChunk)
        is_filter_chunk = issubclass(self.chunk.__class__, FilterChunk)
        self.new_chunk.set_sensitive(is_format_chunk)
        self.new_filter.set_sensitive(is_format_chunk)
        self.convert.set_sensitive(is_format_chunk or is_filter_chunk)
        self.set_format.set_sensitive(is_format_chunk)

#        can_delete = ()
#        if not can_delete:
        chunks = self.chunk.getParent().getChunks()
        if self.chunk.getParent().getParent() != None:
            can_delete = (1 < len(chunks)) or not is_format_chunk
        else:
            can_delete = chunks.index(self.chunk) < (len(chunks)-1) or not is_format_chunk

        self.delete_chunk.set_sensitive(can_delete)
        self.popup.popup( None, None, None, event.button, event.time)

    def onDeleteChunk(self, event):
        self.chunk.getParent().deleteChunk(self.chunk)

    def onConvert(self, event):
        if issubclass(self.chunk.__class__, FormatChunk):
            self.chunk.getParent().convertChunkToFilter(self.chunk)
        elif issubclass(self.chunk.__class__, FilterChunk):
            self.chunk.getParent().convertFilterToChunk(self.chunk)
        else:
            error("Can't convert chunk %s" % self.chunk.id)
        
    def onNewChunk(self, event):
        if self.new_chunk_dlg.runNewChunk() == gtk.RESPONSE_CANCEL: return
        assert issubclass(self.chunk.__class__, FormatChunk)
        format = self.new_chunk_dlg.getFormat()
        id = self.new_chunk_dlg.getId()
        desc = self.new_chunk_dlg.getDescription()
        self.chunk.setFormat(format, "split", id, desc)
        self.chunk.getParent().redisplay()

    def onNewFilter(self, event):
        if self.new_chunk_dlg.runNewChunk() == gtk.RESPONSE_CANCEL: return
        assert issubclass(self.chunk.__class__, FormatChunk) and self.chunk.isString()
        format = self.new_chunk_dlg.getFormat()
        split_format = splitFormat(format)
        size = split_format[1]
        id = self.new_chunk_dlg.getId()
        desc = self.new_chunk_dlg.getDescription()
        self.chunk.getParent().addNewFilter(self.chunk, id, size, desc)

    def onSetFormat(self, event):
        assert issubclass(self.chunk.__class__, FormatChunk)
        if self.new_chunk_dlg.runSetFormat(self.chunk) == gtk.RESPONSE_CANCEL: return
        format = self.new_chunk_dlg.getFormat()
        self.chunk.id = self.new_chunk_dlg.getId()
        self.chunk.description = self.new_chunk_dlg.getDescription()
        try:
            self.chunk.setFormat(format, "rescan")
        except Exception, msg:
            error("Exception while trying to set chunk %s format to \"%s\": %s" \
                % (self.chunk.id, format, msg))
            pass
        self.chunk.getParent().redisplay()
