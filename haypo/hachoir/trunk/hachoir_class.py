from stream.file import FileStream
from plugin import getPluginByStream
from chunk import FilterChunk, FormatChunk
from default import DefaultFilter
from user_filter import UserFilterDescriptor, loadUserFilter
from error import error, warning
from mime import getStreamMime

class Hachoir:
    instance = None
    
    def __init__(self):
        Hachoir.instance = self
        self.display = True
        self.depth = 5
        self.ui = None 
        self._main_filter = None
        self._filter = None
        self.script = None
        self.load_ui = True

    def getFilter(self):
        return self._filter

    def setFilter(self, filter):
#        if self._filter != None:
#            self._filter.purgeCache()
        self._main_filter = filter
        self._filter = filter
        if filter != None:
            if self.load_ui:
                self._filter.display()
                self.ui.window.info.updateFilter(filter)
        else:
            if self.load_ui:
                self.ui.window.clear_table()
        if self.load_ui:
            self.ui.window.updateToolbar()

    def onGoParent(self):
        if self._filter.getParent() == None: return
        self._filter = self._filter.getParent()
        self.ui.window.info.updateFilter(self._filter)
        self._filter.display()
        
    def onRowClick(self, chunk_id):
        if chunk_id == None: return
        chunk = self._filter.getChunk(chunk_id)
        if issubclass(chunk.__class__, FilterChunk):
            filter = chunk.getFilter()
            self.setFilter (filter)

    def loadUser(self, filename):
        try:
            old_filter = self._filter
            old_size = old_filter.getSize()
            user = UserFilterDescriptor(xml_file=filename)
            stream = self._filter.getStream()
            parent = self._filter.getParent()
            stream.seek(self._filter.getAddr())
            new_filter = loadUserFilter(user, stream, parent)
        except Exception, err:
            error("Error while loading user XML filter \"%s\":\n%s" % (filename, err))
            return
        self._filter = new_filter           
        if parent == None:
            self._main_filter = self._filter
            self._addPadding()
        else:
            chunk = old_filter.filter_chunk
            chunk.setFilter(self._filter)
            diff_size = self._filter.getSize() - old_size
            chunk.getParent().rescan(chunk, diff_size)
        if self.load_ui:
            self._filter.display()
        self.ui.window.updateToolbar()
    
    def saveUser(self, filename):
        my = UserFilterDescriptor(filter=self._filter)
        my.writeIntoXML(filename)
    
    def exportUser(self, filename):
        my = UserFilterDescriptor(filter=self._filter)
        my.exportPython(filename)
        
    def _addPadding(self):
        filter_size = self._main_filter.getSize()
        stream_size = self._main_filter.getStream().getSize()
        diff_size = filter_size - stream_size
        if diff_size < 0:
            self._main_filter.read("end", "Raw data", (FormatChunk, "string[%u]" % -diff_size))

    def loadFile(self, filename):
        try:
            print "Load file %s" % filename
            file = open(filename, 'r')
            stream = FileStream(file, filename)
        except IOError, err:
            error("Can't load file %s:\n%s" % (filename, err))
            return
        self.loadStream(stream, filename)

    def loadStream(self, stream, filename=None):
        # Look for a plugin
        split_class = getPluginByStream(stream, filename, None)
        if split_class == None:
            mimes = [ item[0] for item in getStreamMime(stream, filename)]
            warning("Warning: No plugin found for MIME %s." % ", ".join(mimes))
            split_class = DefaultFilter
            
        # Split 
        try:
            stream.seek(0)
            filter = split_class(stream, None)
        except Exception, msg:
            error("Exception while processing file %s:\n%s" \
                % (filename, msg))
            stream.seek(0)
            filter = DefaultFilter(stream)
        self._main_filter = filter
        self._addPadding()
        self.setFilter(filter)

    def loadScript(self, filename):
        try:
            f = open(self.script, 'r')
            script = f.read()
            f.close()
            compiled = compile(script, self.script, 'exec')
            exec compiled
        except Exception, msg:
            error("Exception while loading script \"%s\":\n%s\n%s" \
                % (filename, msg))

    def run(self, filename):
        if self.script:
            self.loadScript(self.script)
        elif filename != None:
            self.loadFile(filename)
        if self.load_ui:
            print "Run user interface ..."
            self.ui.run()      
