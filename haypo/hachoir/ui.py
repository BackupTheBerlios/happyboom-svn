import os
import pygtk
pygtk.require ('2.0')
import gtk
import gtk.glade
from ui_popup import TablePopup

def loadInterface(hachoir):
    global ui 
    glade = os.path.join(os.path.dirname(__file__), 'hachoir.glade')
    ui = GladeInterface(glade, hachoir)

class GladeInterface:
    def __init__(self, filename, hachoir):
        self.hachoir = hachoir
        self.glade_xml = filename
        self.on_row_click = None # event(chunk_id)
        self.on_go_parent = None # event(chunk_id)
        self.about_dialog = None
        self.build_ui()

    def getTableChunk(self, col):
        chunk_id = self.table_store[col][3]
        if chunk_id == None: return None
        return self.hachoir.filter.getChunk(chunk_id)

    def on_treeview_button_press_event(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo != None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor( path, col, 0)
                self.table_popup.show(pthinfo, event)
            return 1

    def run(self):
        try:
            gtk.main()
        except KeyboardInterrupt:
            print "Interrupted (CTRL+C)."

    def updateStatusBar(self, text):
        self.statusbar.push(self.statusbar_state, text)
        
    def enableParentButton(self, enable):
        self.toolbutton_parent.set_sensitive(enable)

    def clear_table(self):
        self.table_store.clear()

    def set_table_value(self, iter, column, value):
        row = self.table_store[iter]
        row[column] = value
       
    def add_table_child(self, parent, addr, size, format, id, description):
        return self.table_store.append(parent, (addr, format, size, None, id, description, None,))
       
    def add_table(self, parent, addr, size, format, id, description, value):
        self.table_store.append(parent, (addr, format, size, id, value, description, ))
       
    def load_window (self):
        xml = gtk.glade.XML(self.glade_xml, "window")
        self.window = xml.get_widget('window')
        self.statusbar = xml.get_widget('statusbar')
        self.toolbar = xml.get_widget('toolbar')
        self.toolbutton_parent = xml.get_widget('toolbutton_parent')
        self.statusbar_state = self.statusbar.get_context_id("State")
        self.table = xml.get_widget('table')
        self.table_store = None
        xml.signal_autoconnect(self)
        
    def build_ui(self):
        self.load_window()
        self.table_popup = TablePopup(self, self.glade_xml)
        self.window.connect("key-press-event", self.onKeyUp)
        self.table.connect("button_press_event", self.on_treeview_button_press_event)
        self.window.set_size_request(760,300)
        self.build_table()

    def onKeyUp(self, widget, key, data=None):
        if key.keyval == gtk.keysyms.Escape:
            self.on_go_parent()
        
    def onTableClicked(self, widget, iter, data=None):
        row = self.table_store[iter]
        self.on_row_click(row[3])

    def build_table(self):
        self.table_store = gtk.TreeStore(str, str, int, str, str, str)
        self.table.set_model(self.table_store)
        self.table.connect("row-activated", self.onTableClicked)
        self.treeview_add_column(self.table, "Address", 0)
        self.treeview_add_column(self.table, "Format", 1)
        self.treeview_add_column(self.table, "Size", 2)
        self.treeview_add_column(self.table, "Name", 3)
        self.treeview_add_column(self.table, "Value", 4)
        self.treeview_add_column(self.table, "Description", 5)
        self.table.set_reorderable(True)
        self.treeselection = self.table.get_selection()

    def treeview_add_column(self, treeview, name, num):
        col = gtk.TreeViewColumn(name)
        treeview.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', num)
        treeview.set_search_column(num)
        col.set_sort_column_id(num)
 
    def on_toolbutton_parent(self, widget, data=None):
        self.on_go_parent()

    def on_open_activate(self, widget):
        print "Open (do nothing yet)"
        chooser = gtk.FileChooserDialog( \
            title="Choose file",
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename() 
            self.hachoir.run(filename)
        chooser.destroy()

    def on_about_activate(self, widget):
        if self.about_dialog == None:
            self.about_xml = gtk.glade.XML(self.glade_xml, "about_dialog")
            self.about_dialog = self.about_xml.get_widget('about_dialog')
        self.about_dialog.show()

    def on_quit_activate(self, widget):
        self.quit()

    def on_window_destroy(self, widget, data=None):
        self.quit()

    def quit(self):
        print "Quit."
        gtk.main_quit()

ui = None
