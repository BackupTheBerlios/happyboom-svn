import os
import pygtk
pygtk.require ('2.0')
import gtk
import gtk.glade

def loadInterface():
    global ui 
    glade = os.path.join(os.path.dirname(__file__), 'hachoir.glade')
    ui = GladeInterface(glade)

class GladeInterface:
    def __init__(self, filename):
        self.on_row_click = None # event(chunk_id)
        self.on_go_parent = None # event(chunk_id)
        self.xml = gtk.glade.XML(filename)
        self.xml.signal_autoconnect(self)
        self.window = self.xml.get_widget('window')
        self.about_window = self.xml.get_widget('about_window')
        self.statusbar = self.xml.get_widget('statusbar')
        self.toolbar = self.xml.get_widget('toolbar')
        self.toolbutton_parent = self.xml.get_widget('toolbutton_parent')
        self.statusbar_state = self.statusbar.get_context_id("State")
        self.window.connect("key-press-event", self.onKeyUp)
        self.table = self.xml.get_widget('table')
        self.table_store = None
        self.build_him()

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
       
    def add_table_child(self, parent, addr, size, type, id, description):
        return self.table_store.append(parent, ("%08X" % addr, type, size, None, id, description, None,))
       
    def add_table(self, parent, addr, size, type, id, description, value):
        self.table_store.append(parent, ("%08X" % addr, type, size, id, value, description, ))
       
    def build_him(self):
        self.window.set_size_request(600,400)
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
        self.treeview_add_column(self.table, "Type", 1)
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

    def on_about_activate(self, widget):
        print "About (do nothing yet)"
        self.about_window.show()

    def on_quit_activate(self, widget):
        self.quit()

    def on_window_destroy(self, widget, data=None):
        self.quit()

    def quit(self):
        print "Quit."
        gtk.main_quit()

ui = None
