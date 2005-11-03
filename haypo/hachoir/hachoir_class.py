from stream import FileStream
from plugin import getPlugin
from chunk import FilterChunk
from default import DefaultFilter, displayDefault
from user_filter import UserFilterDescriptor, loadUserFilter
from error import error
from tools import getBacktrace

class Hachoir:
    instance = None
    
    def __init__(self):
        Hachoir.instance = self
        self.verbose = False
        self.display = True
        self.depth = 5
        self.ui = None 
        self.main_filter = None
        self.script = None

    def onGoParent(self):
        if self.filter.getParent() == None: return
        self.filter = self.filter.getParent()
        self.filter.display()
        
    def onRowClick(self, chunk_id):
        if chunk_id == None: return
        chunk = self.filter.getChunk(chunk_id)
        if issubclass(chunk.__class__, FilterChunk):
            self.filter = chunk.getFilter()
            self.filter.display()

    def loadUser(self, filename):
        try:
            old_filter = self.filter
            old_size = old_filter.getSize()
            user = UserFilterDescriptor(xml_file=filename)
            stream = self.filter.getStream()
            parent = self.filter.getParent()
            stream.seek(self.filter.getAddr())
            new_filter = loadUserFilter(user, stream, parent)
        except Exception, err:
            error("Error while loading user XML filter \"%s\":\n%s" % (filename, err))
            return
        self.filter = new_filter           
        if parent == None:
            self.main_filter = self.filter
            self._addPadding()
        else:
            chunk = old_filter.filter_chunk
            chunk.setFilter(self.filter)
            diff_size = self.filter.getSize() - old_size
            chunk.getParent().rescan(chunk, diff_size)
        self.filter.display()
        self.ui.window.updateToolbar()
    
    def saveUser(self, filename):
        my = UserFilterDescriptor(filter=self.filter)
        my.writeIntoXML(filename)
    
    def exportUser(self, filename):
        my = UserFilterDescriptor(filter=self.filter)
        my.exportPython(filename)
        
    def _addPadding(self):
        size = self.filter.getSize()
        diff_size = (size - self.filter.getStream().getSize())
        if diff_size < 0:
            chunks = self.filter.getChunks()
            if len(chunks) != 0:
                last_chunk = chunks[-1]
            else:
                last_chunk = None
            self.filter.addRawChunk(last_chunk, "end", "{@end@}", "")

    def load(self, filename):
        try:
            stream = FileStream(filename)
        except IOError, err:
            error("Can't load file %s:\n%s" % (filename, err))
            return

        # Look for a plugin
        plugin = getPlugin(filename)
        if plugin == None:
            regex, plugin_name, split_func, display_func = None, "default", DefaultFilter, displayDefault 
        else:
            regex, plugin_name, split_func, display_func = plugin
            
        # Split 
        try:
            filter = split_func(stream)
        except Exception, msg:
            error("Exception while processing file %s with filter %s:\n%s" \
                % (filename, plugin_name, msg))
            raise
            return
        self.main_filter = self.filter = filter
        self._addPadding()
        self.filter.display()

        # Display
        if self.display and display_func != None:
            display_func(self.filter)
        self.ui.window.updateToolbar()

    def loadScript(self, filename):
        try:
            f = open(self.script, 'r')
            script = f.read()
            f.close()
            compiled = compile(script, self.script, 'exec')
            exec compiled
        except Exception, msg:
            error("Exception while loading script \"%s\":\n%s\n%s" \
                % (filename, msg, getBacktrace()))

    def run(self, filename):
        if self.script:
            self.loadScript(self.script)
        elif filename != None:
            self.load(filename)
        self.ui.run()      
