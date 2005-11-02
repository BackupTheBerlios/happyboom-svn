import os
import pygtk
pygtk.require ('2.0')
import gtk
import gtk.glade

class MainWindow:
    def __init__(self, ui):
        self.ui = ui
        xml = gtk.glade.XML(self.ui.glade_xml, "main_window")
        self.window = xml.get_widget('main_window')
        self.statusbar = xml.get_widget('statusbar')
        self.toolbar = xml.get_widget('toolbar')
        self.toolbutton_parent = xml.get_widget('toolbutton_parent')
        self.toolbutton_new = xml.get_widget('toolbutton_new')
        self.toolbutton_open = xml.get_widget('toolbutton_open')
        self.toolbutton_save = xml.get_widget('toolbutton_save')
        self.toolbutton_property = xml.get_widget('toolbutton_property')
        self.statusbar_state = self.statusbar.get_context_id("State")
        self.table = xml.get_widget('table')
        self.table_store = None
        xml.signal_autoconnect(self)
        self.window.connect("key-press-event", self.onKeyUp)
        self.table.connect("button_press_event", self.on_treeview_button_press_event)
        self.window.set_size_request(760,500)
        self.build_table()
        
    def updateToolbar(self):
        file_present = (self.ui.hachoir.main_filter != None)
        self.toolbutton_open.set_sensitive(file_present)
        self.toolbutton_save.set_sensitive(file_present)
        if not file_present:
            self.toolbutton_parent.set_sensitive(False)
        self.toolbutton_property.set_sensitive(file_present)

    def getTableChunk(self, col):
        chunk_id = self.table_store[col][3]
        if chunk_id == None: return None
        return self.ui.hachoir.filter.getChunk(chunk_id)

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
                self.ui.table_popup.show(pthinfo, event)
            return 1

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

    def onKeyUp(self, widget, key, data=None):
        if key.keyval == gtk.keysyms.Escape:
            self.on_go_parent()
        
    def onTableClicked(self, widget, iter, data=None):
        row = self.table_store[iter]
        self.ui.on_row_click(row[3])

    def build_table(self):
        self.table_store = gtk.TreeStore(int, str, int, str, str, str)
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
        self.ui.on_go_parent()

    def on_toolbutton_new(self, widget):
        self.on_open_activate(widget)

    def on_toolbutton_property(self, widget):
        filter = self.ui.hachoir.filter
        dlg = self.ui.property_dialog
        if dlg.run(filter) == gtk.RESPONSE_CANCEL: return
        filter.setId( dlg.getId() )
        filter.setDescription( dlg.getDescription() )
        filter.updateStatusBar()
        
    def on_open_activate(self, widget):
        chooser = gtk.FileChooserDialog( \
            title="Choose file to split",
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename() 
            self.ui.hachoir.load(filename)
        chooser.destroy()

    def on_toolbutton_open(self, widget):
        chooser = gtk.FileChooserDialog( \
            title="Choose filter",
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename() 
            self.ui.hachoir.loadUser(filename)
        chooser.destroy()

    def on_toolbutton_export(self, widget):
        chooser = gtk.FileChooserDialog( \
            title="Export current filter to python script ...",
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename() 
            self.ui.hachoir.exportUser(filename)
        chooser.destroy()

    def on_toolbutton_save(self, widget):
        chooser = gtk.FileChooserDialog( \
            title="Save XML filter into ...",
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename() 
            self.ui.hachoir.saveUser(filename)
        chooser.destroy()

    def on_about_activate(self, widget):
        self.ui.about_dialog.show()

    def on_quit_activate(self, widget):
        self.ui.quit()

    def on_window_destroy(self, widget, data=None):
        self.ui.quit()
