import pygtk
import gtk
import gtk.glade

class NewStringDialog:
    def __init__(self, filename):
        xml = gtk.glade.XML(filename, "new_string")
        self.window = xml.get_widget('new_string')
        self.window.hide()
        xml.signal_autoconnect(self)
        self.format_widget = xml.get_widget("format")
        self.id_widget = xml.get_widget("identifier")
        self.desc_widget = xml.get_widget("description")

    def getId(self):
        return self.id_widget.get_text()

    def getDescription(self):
        return self.desc_widget.get_text()

    def getFormat(self):
        return self.format_widget.child.get_text()

    def run(self):
        r = self.window.run()
        self.window.hide()
        return r
