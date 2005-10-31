from filter import Filter
from chunk import ArrayChunk, FilterChunk
from xml.dom.minidom import getDOMImplementation, parse
from program import VERSION

class UserChunk:
    def __init__(self, id, format, description):
        self.id = id
        self.format = format
        self.description = description
        
    def __str__(self):
        return "UserChunk <id=%s, format=%s, description=%s>" % \
            (self.id, self.format, self.description)

class UserSubChunk(UserChunk):
    def __init__(self, id, sub, sub_format, description):
        UserChunk.__init__(self, id, "sub", description)
        self.sub = sub
        self.sub_format = sub_format

class UserFilter(Filter):
    def __init__(self, descriptor, stream):
        Filter.__init__(self, "user_filter", "User filter", stream)
        for chunk in descriptor.chunks:
            if chunk.format == "sub":
                print "Sub %s" % chunk.sub_format
#                format = chunk.sub_format.split('.')
#                module = ".".join(format[:-1])
#                format = format[-1]
                #__import__(module, globals(), locals(), [format])
                mod = __import__("plugins.png", globals(), locals(), ["PngChunk"])
                print mod.PngChunk
                chunk_class = mod.PngChunk
                self.readChild(chunk.id, chunk_class, chunk.description)
                print "Sub ok"
            else:
                self.read(chunk.id, chunk.format, chunk.description)
            print "- End chunk"
        print "- End end"

class UserFilterDescriptor:
    def __init__(self, filter=None, xml_file=None):
        self.chunks = []
        if filter != None:
            self.createFromFilter(filter)
        elif xml_file != None:
            self.createFromXML(xml_file)
            
    def createFromXML(self, filename):
        xml = parse(filename)
        self.chunks = []
        self.__loadXML(xml.documentElement)
        
    def __loadXML(self, node):
        for chunk in node.childNodes:
            if chunk.nodeType == chunk.ELEMENT_NODE and chunk.tagName == "chunk":
                id = chunk.getAttribute("id") 
                description = chunk.getAttribute("description") 
                format = chunk.getAttribute("format")
                
                if format == "sub":
                    sub_format = chunk.getAttribute("sub_format") 
                    sub = UserFilterDescriptor()
                    sub.__loadXML(chunk)
                    user_chunk = UserSubChunk(id, sub, sub_format, description)
                else:
                    user_chunk = UserChunk(id, format, description)
                self.chunks.append(user_chunk)

    def toXML(self):
        impl = getDOMImplementation()
        doc = impl.createDocument(None, "user_filter", None)
        root = doc.documentElement
        root.setAttribute("hachoir_version", VERSION)
        self.__toXML(doc, root)
        return doc

    def __toXML(self, doc, node):
        for chunk in self.chunks:
            item = doc.createElement("chunk")
            item.setAttribute("id", chunk.id)
            item.setAttribute("description", chunk.description)
            item.setAttribute("format", chunk.format)
            node.appendChild(item)
            if issubclass(chunk.__class__, UserSubChunk):
                item.setAttribute("sub_format", chunk.sub_format)
                chunk.sub.__toXML(doc, item)

    def createFromFilter(self, filter):
        self.chunks = []
        self.__createFromChunks(filter.getChunks())

    def __createFromChunks(self, chunks):
        for chunk in chunks:
            if issubclass(chunk.__class__, ArrayChunk):
                self.__createFromChunks(chunk)
            else:
                if issubclass(chunk.__class__, FilterChunk):
                    format = str(chunk.getFilter().__class__)
                    sub = UserFilterDescriptor(filter=chunk.getFilter())
                    user = UserSubChunk(chunk.id, sub, format, chunk.description)
                else:
                    user = UserChunk(chunk.id, chunk.getFormat(), chunk.description)
                self.chunks.append(user)
