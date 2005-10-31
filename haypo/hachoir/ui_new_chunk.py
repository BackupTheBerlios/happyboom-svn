import pygtk
pygtk.require ('2.0')
import gtk
import gtk.glade
from format import splitFormat

class NewChunkDialog:
    def __init__(self, filename):
        xml = gtk.glade.XML(filename, "new_chunk")
        self.window = xml.get_widget('new_chunk')
        self.window.hide()
        xml.signal_autoconnect(self)
        self.label_widget = xml.get_widget("label")
        self.size_widget = xml.get_widget("size")
        self.endian_widget = xml.get_widget("endian")
        self.format_widget = xml.get_widget("format")
        self.id_widget = xml.get_widget("identifier")
        self.desc_widget = xml.get_widget("description")
        self.response = gtk.RESPONSE_CANCEL

    def getId(self):
        return self.id_widget.get_text()

    def getDescription(self):
        return self.desc_widget.get_text()

    def getFormat(self):
        size = self.size_widget.get_text()
        endian = self.endian_widget.child.get_text()
        type = self.format_widget.child.get_text()
        return "%s%s%s" % (endian, size, type)

    def runNewChunk(self):
        # TODO: i18n the text
        self.window.set_title("New chunk")
        self.label_widget.set_text("Choose a chunk format for the new chunk:")
        self.size_widget.set_text("1")
        self.endian_widget.child.set_text("!")
        self.format_widget.child.set_text("s")
        self.id_widget.set_text("raw")
        self.desc_widget.set_text("Raw")
        r = self.window.run()
        self.window.hide()
        return r

    def runSetFormat(self, chunk):
        # TODO: i18n the text
        self.window.set_title("Set chunk format")
        self.label_widget.set_text("Set chunk %s format to:" % chunk.id)
        format = chunk.getFormat()
        split = splitFormat(format)
        if split != None:
            self.size_widget.set_text(split[1])
            self.endian_widget.child.set_text(split[0])
            self.format_widget.child.set_text(split[2])
        self.id_widget.set_text(chunk.id)
        self.desc_widget.set_text(chunk.description)
        r = self.window.run()
        self.window.hide()
        return r
