import os
import pygtk
pygtk.require ('2.0') # 2.2 for Clipboard
import gtk
import gtk.glade

def loadInterface(hachoir):
    global ui 
    global window
    glade = os.path.join(os.path.dirname(__file__), 'hachoir.glade')
    ui = GladeInterface(glade, hachoir)
    window = ui.window
    hachoir.ui = ui 
    hachoir.ui.on_row_click = hachoir.onRowClick
    hachoir.ui.on_go_parent = hachoir.onGoParent

class GladeInterface:
    def __init__(self, filename, hachoir):
        self.hachoir = hachoir
        self.glade_xml = filename
        self.on_row_click = None # event(chunk_id)
        self.on_go_parent = None # event(chunk_id)
        self.build_ui()
        self._clipboard = None
        
    def getClipboard(self):
        if self._clipboard == None:
            self._clipboard = gtk.Clipboard()
        return self._clipboard

    def run(self):
        self.window.updateToolbar()
        try:
            gtk.main()
        except KeyboardInterrupt:
            print "Interrupted (CTRL+C)."

    def loadAbout(self):
        xml = gtk.glade.XML(self.glade_xml, "about_dialog")
        self.about_dialog = xml.get_widget('about_dialog')
        self.about_dialog.hide()
        
    def build_ui(self):
        from ui_window import MainWindow
        from ui_popup import TablePopup
        from ui_property import PropertyDialog
        self.window = MainWindow(self)
        self.loadAbout()
        self.table_popup = TablePopup(self, self.glade_xml)
        self.property_dialog = PropertyDialog(self)
        
    def quit(self):
        print "Quit."
        gtk.main_quit()

ui = None
window = None
