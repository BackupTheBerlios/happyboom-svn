from stream import FileStream
from plugin import getPlugin
from chunk import FilterChunk
from default import DefaultFilter, displayDefault
from user_filter import UserFilterDescriptor, UserFilter
from xml.dom.ext import PrettyPrint

class Hachoir:
    def __init__(self):
        self.verbose = False
        self.display = True
        self.depth = 5

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

    def loadUser(self, xml_filename, stream):
        user = UserFilterDescriptor(xml_file=xml_filename)
        self.filter = UserFilter(user, stream)
        self.filter.display()
    
    def run(self, filename):
        # Create stream
        stream = FileStream(filename)
#        self.loadUser("user.xml", stream); return

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

        # Display
        if self.display:
            print "=== File %s data ===" % filename
            display_func(self.filter)
        return True

