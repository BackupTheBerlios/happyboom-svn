import pygtk
import gtk
import gtk.glade

class PropertyDialog:
    def __init__(self, ui):
        self.ui = ui
        xml = gtk.glade.XML(self.ui.glade_xml, "filter_property")
        self.window = xml.get_widget("filter_property")
        self.window.hide()
        xml.signal_autoconnect(self)
        self.id_widget = xml.get_widget("id")
        self.desc_widget = xml.get_widget("description")

    def getId(self):
        return self.id_widget.get_text()

    def getDescription(self):
        return self.desc_widget.get_text()

    def run(self, filter):
        self.id_widget.set_text(filter.getId())
        self.desc_widget.set_text(filter.getDescription())
        r = self.window.run()
        self.window.hide()
        return r
