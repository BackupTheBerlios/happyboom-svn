import os
import pygtk
import gtk
import gtk.glade
import config
from tools import convertDataToPrintableString

class InfoNotebook:
    def __init__(self, xml):
        self.filter_name = xml.get_widget("filter_name")
        self.filter_description = xml.get_widget("filter_description")
        self.filter_type = xml.get_widget("filter_type")
        self.filter_path = xml.get_widget("filter_path")
        
        self.stream_type = xml.get_widget("stream_type")        
        self.stream_size = xml.get_widget("stream_size")
        
        self.chunk_name = xml.get_widget("chunk_name")
        self.chunk_description = xml.get_widget("chunk_description")
        self.chunk_size = xml.get_widget("chunk_size")
        self.chunk_address = xml.get_widget("chunk_address")
        self.chunk_type = xml.get_widget("chunk_type")
        
    def updateChunk(self, chunk):
        if chunk != None:
            self.chunk_name.set_text(chunk.id)
            self.chunk_description.set_text(chunk.description)
            self.chunk_address.set_text(str(chunk.addr))
            self.chunk_size.set_text(str(chunk.size))
            self.chunk_type.set_text(chunk.getFormat())
        chunk_present = (chunk != None)
        self.info_chunk_save = chunk_present
        self.info_chunk_delete = chunk_present
    
    def updateFilter(self, filter):        
        self.filter_name.set_text(filter.getId())
        self.filter_description.set_text(filter.getDescription())
        self.filter_type.set_text(filter.__class__.__name__)
        self.filter_path.set_text(filter.getPath())

        stream = filter.getStream()
        self.stream_type.set_text(stream.getType())
        self.stream_size.set_text("%u" % filter.getSize())

class MainWindow:
    def __init__(self, ui):
        self.ui = ui
        xml = gtk.glade.XML(self.ui.glade_xml, "main_window")
        self.window = xml.get_widget('main_window')
        self.toolbar = xml.get_widget('toolbar')
        self.toolbutton_parent = xml.get_widget('toolbutton_parent')
        self.toolbutton_open = xml.get_widget('toolbutton_open')
        self.toolbutton_close = xml.get_widget('toolbutton_close')
        self.ascii_path = xml.get_widget('ascii_path')
        self.ascii_content = xml.get_widget('ascii_content')
        self.hexa_path = xml.get_widget('hexa_path')
        self.hexa_content = xml.get_widget('hexa_content')
        self.menu_close = xml.get_widget('menu_close')
#        self.info_filter_open = xml.get_widget('info_filter_open')
#        self.info_filter_save = xml.get_widget('info_filter_save')
#        self.info_filter_export = xml.get_widget('info_filter_export')
#        self.info_filter_property = xml.get_widget('info_filter_property')
        self.info = InfoNotebook(xml)
        self.table = xml.get_widget('table')
        self.table_store = None
        xml.signal_autoconnect(self)
        self.window.connect("key-press-event", self.onKeyUp)
        self.table.connect("button_press_event", self.on_treeview_button_press_event)
        self.window.set_size_request(600,560)

        self.field_show_format = False 
        self.row_chunk_id = None
        self.sort_column_as_long = True
        self.build_table()
        
    def onChunkCopy(self, event):
        chunk = self.getActiveChunk()
        assert chunk != None
        text = chunk.getStringValue()
        self.ui.getClipboard().set_text(text)

    def onSaveChunk(self, event):
        chunk = self.getActiveChunk()
        assert chunk != None

        chooser = gtk.FileChooserDialog( \
            title="Write chunk data to ...",
            parent=self.window,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename() 
            raw = chunk.getRaw()
            f = open(filename, 'w')
            f.write(raw)
            f.close()
        chooser.destroy()

    def onDeleteChunk(self, event):
        chunk = self.getActiveChunk()
        chunk.getParent().deleteChunk(chunk)
        
    def updateToolbar(self):
        file_present = (self.ui.hachoir.getFilter() != None)
        filter_present = file_present
        if not file_present:
            self.toolbutton_parent.set_sensitive(False)
        self.toolbutton_close.set_sensitive(file_present)
#        self.info_filter_open.set_sensitive(filter_present)
#        self.info_filter_save.set_sensitive(filter_present)
#        self.info_filter_export.set_sensitive(filter_present)
#        self.info_filter_property.set_sensitive(filter_present)
        self.menu_close.set_sensitive(file_present)

    def getTableChunk(self, col):
        chunk_id = self.table_store[col][self.row_chunk_id]
        if chunk_id == None: return None
        return self.ui.hachoir.getFilter().getChunk(chunk_id)

    def on_treeview_button_press_event(self, treeview, event):
        return
        # TODO: Re-enable popup menu :-)
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

    def enableParentButton(self, enable):
        self.toolbutton_parent.set_sensitive(enable)

    def clear_table(self):
        self.table_store.clear()
        if self.sort_column_as_long:
            self.table_store.set_sort_column_id(-1, gtk.SORT_ASCENDING)
        self.table.columns_autosize()

    def set_table_value(self, iter, column, value):
        row = self.table_store[iter]
        row[column] = value
       
    def add_table_child(self, parent, addr, size, format, id, description):
        if self.field_show_format:
            data = (addr, format, size, None, id, description, None,)
        else:
            data = (addr, size, None, id, description, None,)
        return self.table_store.append(parent, data)
       
    def update_table(self, filter, ROW, parent, addr, size, format, id, description, value):
        if filter != self.ui.hachoir.getFilter():
            return
        addr = str(addr)
        size = str(size)
        if self.field_show_format:
            data = (addr, format, size, id, value, description)
        else:
            data = (addr, size, id, value, description)
        self.table_store[ROW] = data 

    def add_table(self, parent, addr, size, format, id, description, value):
        addr = str(addr)
        size = str(size)
        if self.field_show_format:
            data = (addr, format, size, id, value, description, )
        else:
            data = (addr, size, id, value, description, )
        return self.table_store.append(parent, data)

    def onKeyUp(self, widget, key, data=None):
        if key.keyval == gtk.keysyms.Escape:
            self.ui.on_go_parent()
        
    def onTableRowActivate(self, widget, iter, data=None):
        row = self.table_store[iter]
        self.ui.on_row_click(row[self.row_chunk_id])
        
    def getActiveChunk(self):
        select = self.table.get_selection()
        iter = select.get_selected()[1]
        if iter != None:
            row = self.table_store[iter]
            return self.ui.hachoir.getFilter().getChunk(row[self.row_chunk_id])
        else:
            return None 

    def onTableClick(self, widget, data=None):
        chunk = self.getActiveChunk()
        self.info.updateChunk(chunk)

    def build_table(self):
        types = [str, str, str, str, str]
        if self.field_show_format:
            types.append(str)
        self.table_store = gtk.TreeStore(*types)
        self.table.set_model(self.table_store)
        self.table.connect("cursor-changed", self.onTableClick)
        self.table.connect("row-activated", self.onTableRowActivate)

        i = 0
        self.treeview_add_column(self.table, "Address", i)
        if self.sort_column_as_long:
            self.table_store.set_sort_func(0, self.cmpColumnsLong, i)
        i += 1
        if self.field_show_format:
            i = self.treeview_add_column(self.table, "Format", i)
        self.treeview_add_column(self.table, "Size", i)
        if self.sort_column_as_long:
            self.table_store.set_sort_func(i, self.cmpColumnsLong, i)
        i += 1
        self.row_chunk_id = i
        i = self.treeview_add_column(self.table, "Name", i)
        i = self.treeview_add_column(self.table, "Value", i)
        i = self.treeview_add_column(self.table, "Description", i)
        if self.sort_column_as_long:
            self.table_store.set_default_sort_func(self.cmpDefault)
        self.table.columns_autosize()

    def cmpDefault(self, model, a, b):
        return 0

    def cmpColumnsLong(self, model, a, b, row_id):
        a = model[a][row_id]
        b = model[b][row_id]
        if a != None and b != None:
            return cmp( long(a) , long(b) )
        else:
            return 0

    def treeview_add_column(self, treeview, name, num):
        col = gtk.TreeViewColumn(name)
        treeview.append_column(col)
        cell = gtk.CellRendererText()
        col.pack_start(cell, True)
        col.add_attribute(cell, 'text', num)
        treeview.set_search_column(num)
        col.set_sort_column_id(num)
        return num+1

    def on_toolbutton_purge_cache(self, widget, data=None):
        from cache import CacheList
        CacheList.getInstance().purgeCaches()
 
    def on_toolbutton_parent(self, widget, data=None):
        self.ui.on_go_parent()

    def on_toolbutton_new(self, widget):
        self.on_open_activate(widget)

    def on_toolbutton_close(self, widget):
        dlg = gtk.MessageDialog( \
            type=gtk.MESSAGE_QUESTION,
            parent=self.window,
            buttons=gtk.BUTTONS_YES_NO,
            message_format="Are you sure that you want to close the file?")
        dlg.set_default_response(gtk.RESPONSE_NO)            
        if dlg.run() == gtk.RESPONSE_YES:
            self.ui.hachoir.setFilter(None)
        dlg.destroy()

    def on_toolbutton_property(self, widget):
        filter = self.ui.hachoir.getFilter()
        dlg = self.ui.property_dialog
        if dlg.run(filter) == gtk.RESPONSE_CANCEL: return
        filter.setId( dlg.getId() )
        filter.setDescription( dlg.getDescription() )
        
    def on_open_activate(self, widget):
        chooser = gtk.FileChooserDialog( \
            title="Choose file to split",
            parent=self.window,
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename() 
            self.ui.hachoir.loadFile(filename)
        chooser.destroy()

    def on_toolbutton_open(self, widget):
        chooser = gtk.FileChooserDialog( \
            title="Choose filter",
            parent=self.window,
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename() 
            self.ui.hachoir.loadUser(filename)
        chooser.destroy()

    def on_toolbutton_export(self, widget):
        chooser = gtk.FileChooserDialog( \
            title="Export current filter to python script ...",
            parent=self.window,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename() 
            self.ui.hachoir.exportUser(filename)
        chooser.destroy()

    def on_toolbutton_save(self, widget):
        chooser = gtk.FileChooserDialog( \
            title="Save XML filter into ...",
            parent=self.window,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename() 
            self.ui.hachoir.saveUser(filename)
        chooser.destroy()

    def on_ascii_clicked(self, widget):
        chunk = self.getActiveChunk()
        if chunk == None:
            return
        path = chunk.getParent().getPath()+"/"+chunk.id
        self.ascii_path.set_text(path)
        raw = chunk.getRaw(config.max_ascii_length)
        content = convertDataToPrintableString(raw, True)
        if config.max_hexa_length < chunk.size:
            if len(content) != 0:
                content = content + "\n"
            content = content + " (...)"
        # TODO: Write new TextBuffer!?
        buffer = gtk.TextBuffer()
        buffer.set_text(content)
        self.ascii_content.set_buffer(buffer)

    def on_hexadecimal_clicked(self, widget):
        chunk = self.getActiveChunk()
        if chunk == None:
            return
        path = chunk.getParent().getPath()+"/"+chunk.id
        self.hexa_path.set_text(path)
        raw = chunk.getRaw(config.max_hexa_length)
        # TODO: Use better str=>hexa function ...
        content = ""
        wrap = 16
        addr = 0
        while len(raw) != 0:
            if len(content) != 0:
                content = content + "\n"
            content = content + "% 4s: " % addr + " ".join([ "%02X" % ord(i) for i in raw[:wrap] ])
            addr = addr + wrap
            raw = raw[wrap:]
        if config.max_hexa_length < chunk.size:
            if len(content) != 0:
                content = content + "\n"
            content = content + " (...)"
        # TODO: Write new TextBuffer!?
        buffer = gtk.TextBuffer()
        buffer.set_text(content)
        self.hexa_content.set_buffer(buffer)

    def on_about_activate(self, widget):
        self.ui.about_dialog.show()

    def on_quit_activate(self, widget):
        self.ui.quit()

    def on_window_destroy(self, widget, data=None):
        self.ui.quit()
