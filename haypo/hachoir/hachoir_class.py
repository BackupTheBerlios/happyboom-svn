from stream import FileStream
from plugin import getPlugin
from chunk import FilterChunk
from default import DefaultFilter, displayDefault
from user_filter import UserFilterDescriptor, UserFilter

class Hachoir:
    def __init__(self):
        self.verbose = False
        self.display = True
        self.depth = 5
        self.ui = None 
        self.main_filter = None

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
        stream = self.main_filter.getStream()
        stream.seek(0)
        user = UserFilterDescriptor(xml_file=filename)
        self.filter = UserFilter(user, stream)
        self.main_filter = self.filter
        self.filter.display()
        self.ui.updateToolbar()
    
    def saveUser(self, filename):
        my = UserFilterDescriptor(filter=self.main_filter)
        my.writeIntoXML(filename)
        
    def load(self, filename):
        stream = FileStream(filename)

        # Look for a plugin
        plugin = getPlugin(filename)
        if plugin == None:
            regex, plugin_name, split_func, display_func = None, "default", DefaultFilter, displayDefault 
        else:
            regex, plugin_name, split_func, display_func = plugin
        if self.verbose:
            print "Split file \"%s\": %s." % (filename, plugin_name)
            
        # Split 
        if 0 < self.depth:
            print "=== Split file %s ===" % filename

        self.filter = split_func(stream)
        self.filter.display()
        self.main_filter = self.filter

        # Display
        if self.display:
            print "=== File %s data ===" % filename
            display_func(self.filter)
        self.ui.updateToolbar()

    def run(self, filename):
        if filename != None:
            self.load(filename)
        self.ui.run()      
