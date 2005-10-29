import os
import pygtk
pygtk.require ('2.0')
import gtk
import gtk.glade

def loadInterface():
    global hmi
    glade = os.path.join(os.path.dirname(__file__), 'hachoir.glade')
    hmi = GladeInterface(glade)

class GladeInterface:
    def __init__(self, filename):
        self.xml = gtk.glade.XML(filename)
        self.xml.signal_autoconnect(self)
        self.window = self.xml.get_widget('window')
        self.table = self.xml.get_widget('table')
        self.table_store = None
        self.build_him()

    def run(self):
        try:
            gtk.main()
        except KeyboardInterrupt:
            print "Interrupted (CTRL+C)."

    def set_table_value(self, iter, column, value):
        row = self.table_store[iter]
        row[column] = value
       
    def add_table_child(self, parent, addr, size, id, description):
        return self.table_store.append(parent, ("%08X" % addr, size, None, id, description, None,))
       
    def add_table(self, parent, addr, size, name, id, description, comment):
        self.table_store.append(parent, ("%08X" % addr, size, name, id, description, comment,))
       
    def build_him(self):
        self.window.set_size_request(600,400)
        self.build_table()

    def build_table(self):
        self.table_store = gtk.TreeStore(str, str, str, str, str, str)
        self.table.set_model(self.table_store)
        self.treeview_add_column(self.table, "Address", 0)
        self.treeview_add_column(self.table, "Size", 1)
        self.treeview_add_column(self.table, "Data", 2)
        self.treeview_add_column(self.table, "Name", 3)
        self.treeview_add_column(self.table, "Description", 4)
        self.treeview_add_column(self.table, "Comment", 5)
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
 
    def on_window_destroy(self, widget, data=None):
        self.quit()

    def quit(self):
        print "Quit."
        gtk.main_quit()

hmi = None
