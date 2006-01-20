"""
Base class for all splitter filters.
"""

import re
import config
import ui.ui as ui
from chunk import FormatChunk, FilterChunk, BitsChunk
from error import error
from cache import Cache

class BasicFilter(object):
    regex_chunk_uniq_id = re.compile("^(.*?)([0-9]+)$")

    def __init__(self, identifier, description, stream, parent, addr, endian):
        self._id = identifier
        self._description = description
        self._stream = stream
        self._parent = parent
        self._addr = addr 
        self._chunks_counter = {}
        self._chunks_dict = {}
        self._endian = endian
        self.filter_chunk = None

    @staticmethod
    def getStaticSize(stream, args):
        return None

    def updateParent(self, chunk):
        pass
    def getId(self):
        return self._id
    def setId(self, identifier):
        if self._id == identifier:
            return
        self._id = identifier
        if self.filter_chunk != None:
            self.filter_chunk.id = identifier
    def getDescription(self):
        return self._description
    def setDescription(self, description):
        self._description = description
    def getAddr(self):
        return self._addr
    def getParent(self):
        return self._parent
    def getStream(self):
        return self._stream
    def updateChunkId(self, old_id, new_id):
        pass
    def updateChunkDescription(self, identifier, desc):
        pass
    def updateChunkDisplay(self, identifier):
        pass
    def __len__(self):
        return len(self._chunks_dict)

    def getPath(self):
        """
        Get path to the filter.
        Example: "grandparent > parent > item"
        """
        text = ""
        current = self
        while current != None:
            if text != "":
                text = "/" + text
            text = current.getId() + text
            current = current.getParent()
        return "/"+text

    def _getUniqChunkId(self, root, index):
        if root in self._chunks_counter:
            self._chunks_counter[root] = self._chunks_counter[root] + 1
        else:
            self._chunks_counter[root] = index
        return self._chunks_counter[root]

    def getUniqChunkId(self, identifier):
        # No collision
        if identifier not in self._chunks_dict and identifier[-2:] != "[]":
            return identifier

        # Pattern like "block[]"
        if identifier[-2:] == "[]":
            root = identifier[:-2]
            start = 0
            pattern = "%s[%u]"
        else:
            # Manage identifier collision
            m = BasicFilter.regex_chunk_uniq_id.match(identifier)
            if m != None:
                root = m.group(1)
                start = int(m.group(2)) + 1
            else:
                root = identifier
                start = 2
            pattern = "%s%u"
        if root in self._chunks_counter:
            self._chunks_counter[root] = self._chunks_counter[root] + 1
        else:
            self._chunks_counter[root] = start 
        return pattern % (root, self._chunks_counter[root])
        
    def hasChunk(self, identifier):
        return identifier in self._chunks_dict

    def _getEndian(self):
        return self._endian
    endian = property(_getEndian)

    def addPadding(self, identifier="end", description="Raw end"):
        size = self._stream.getRemainSize()
        if 0 < size:
            self.read(identifier, description, \
                (FormatChunk, "string[%u]" % size))

    # --- Pure virtual methods -----------
    def getSize(self):
        todoWriteMethod(self, "getSize") 
    def __getitem__(self, chunk_id):
        todoWriteMethod(self, "__getitem__") 
    def getChunk(self, chunk_id):
        todoWriteMethod(self, "getChunk")
    def display(self):
        todoWriteMethod(self, "display")

class OnDemandFilter(BasicFilter, Cache):
    def __init__(self, identifier, description, stream, parent, endian=None):
        BasicFilter.__init__(self, identifier, description, stream, parent, \
            stream.tell(), endian)
        Cache.__init__(self, "Filter %s" % identifier)
        self._size = 0
        self._chunks = []
        self._chunks_cache = {}
   
    def getCacheSize(self):
        return len(self._chunks_cache)

    def updateChunkId(self, old_id, new_id):
        # Update self._chunks
        pos = self._chunks.index(old_id)
        assert pos != -1
        self._chunks[pos] = new_id

        # Update self._chunks_dict
        info = self._chunks_dict[old_id]
        info[0] = new_id
        del self._chunks_dict[old_id]
        self._chunks_dict[new_id] = info
        
        # Update self._chunks_dict
        if old_id in self._chunks_cache:
            cache = self._chunks_cache[old_id]
            del self._chunks_cache[old_id]
            self._chunks_cache[new_id] = cache

        # Update display
        self.updateChunkDisplay(new_id)

    def updateChunkDisplay(self, identifier):
        if ui.ui == None:
            return
        pos = self._chunks.index(identifier)
        assert pos != -1
        info = self.displayChunkInfo(identifier)
        ui.window.update_table(self, pos, *info)

    def updateChunkDescription(self, identifier, desc):
        pos = self._chunks.index(identifier)
        assert pos != -1
        self._chunks_dict[identifier][1] = desc
        self.updateChunkDisplay(identifier)

    def purgeCache(self):
        if len(self._chunks_cache) != 0 and config.verbose:
            print "Purge cache: destroy %s chunks" % len(self._chunks_cache)
        self._chunks_cache = {}
        
    def read(self, identifier, description, info, optionnal={}): 
        self._read(identifier, description, info, optionnal, False)

    def _read(self, identifier, description, info, optionnal, instanciate):
        chunk_class = info[0]
        identifier = self.getUniqChunkId(identifier)
        addr = self._stream.tell()
        if issubclass(chunk_class, BasicFilter):
            filter_stream = optionnal.get("stream", self._stream)
            size = optionnal.get("size", None)
            filter_addr = filter_stream.tell()
            args = info[1:]
            if not instanciate and size == None:
                size = chunk_class.getStaticSize(self._stream, info[1:])
            if instanciate or size == None:
                filter = chunk_class(filter_stream, self, *args)
                description = filter.getDescription()
                filter.setId(identifier)
                chunk = FilterChunk(identifier, filter, self, addr)
                size = filter.getSize()
                if config.verbose:
                    print "%s: Instanciate filter %s" % \
                        (self.getPath(), identifier)
            else:
                chunk = None

            chunk_info = [identifier, description, addr, size, \
                    (chunk_class, filter_stream, filter_addr, args), None, {}]
            self._chunks_dict[identifier] = chunk_info
            self._chunks.append(identifier)
            if chunk != None:
                filter.updateParent(chunk)
                self._chunks_cache[identifier] = chunk
            self._size = self._size + size
            self._stream.seek(addr + size)
        else:
            post = optionnal.get("post", None)
            if "post" in optionnal:
                del optionnal["post"]
            if isinstance(info, list):
                args = info[1:]
            else:
                args = [ i for i in info[1:] ]
            instance_info  = [info[0], identifier, description, self._stream]
            instance_info += args
            instance_info += [self]

            if not instanciate:
                size = chunk_class.getStaticSize(self._stream, info[1:])
            else:
                size = None
            if size != None:
                self._stream.seek(size, 1)
            else:
                # Instanciate the chunk
                seek = False
                chunk = info[0] (*instance_info[1:], **optionnal)
                size = chunk.size
                identifier = chunk.id
                self._chunks_cache[identifier] = chunk
            chunk_info = [identifier, description, addr, size, \
                instance_info, post, optionnal]
            self._chunks_dict[identifier] = chunk_info
            self._chunks.append(identifier)
            self._size = self._size + size
        if instanciate:
            return chunk
        else:
            return identifier

    def doRead(self, identifier, description, info, optionnal={}):
        chunk = self._read(identifier, description, info, optionnal, True)
        if isinstance(chunk, FilterChunk):
            return chunk.getFilter()
        else:
            return chunk

    def displayChunkInfo(self, identifier):
        info = self._chunks_dict[identifier]
        chunk_class = info[4][0]
        if issubclass(chunk_class, BasicFilter):
            display = "(...)"
            format = chunk_class.__name__
        else:
            chunk = self.getChunk(identifier)
            display = chunk.getDisplayData()
            format = chunk.getSmallFormat()
        addr = info[2]
        size = info[3]
        return (None, addr, size, format, info[0], info[1], display)

    def display(self):
        ui.window.enableParentButton(self.getParent() != None)
        ui.window.clear_table()
        for identifier in self._chunks:
            info = self.displayChunkInfo(identifier)
            if self._chunks_dict[identifier][4][0] == BitsChunk:
                self.getChunk(identifier).uiDisplay(ui.window)
            else:
                ui.window.add_table(*info)
 
    def getSize(self): return self._size

    def _createInstance(self, identifier):
        description = self._chunks_dict[identifier][1]
        addr = self._chunks_dict[identifier][2]
        size = self._chunks_dict[identifier][3]
        desc = self._chunks_dict[identifier][4]
        post = self._chunks_dict[identifier][5]
        chunks_kw = self._chunks_dict[identifier][6]
        oldpos = self._stream.tell()
        if config.verbose:
            print "%s: Instanciate %s (of type %s)" % \
                (self.getPath(), identifier, desc[0].__name__)
        if not issubclass(desc[0], BasicFilter):
            # Chunk
            chunk_class = desc[0]
            chunk_args = desc[1:]
            self._stream.seek(addr)
            chunk = chunk_class(*chunk_args, **chunks_kw)
            if post != None:
                chunk.display = post(chunk)
        else:
            # Filter
            filter_stream = desc[1]
            if filter_stream != self._stream:
                filter_stream.seek(desc[2])
            else:
                self._stream.seek(addr)
            try:
                filter = desc[0] (filter_stream, self, *desc[3])
                filter.setId(identifier)
                chunk = FilterChunk(identifier, filter, self, addr)
                if filter.getDescription() != desc[1]:
                    self.updateChunkDescription(identifier, filter.getDescription())
                filter.updateParent(chunk)
            except Exception, msg:
                error("Error when loading filter %s: %s" % (identifier, msg))
                if filter_stream != self._stream:
                    filter_stream.seek(desc[2])
                else:
                    self._stream.seek(addr)
                if isinstance(size, int) or isinstance(size, long):
                    self._chunks_dict[identifier][4] = (FormatChunk, identifier, description, \
                        filter_stream, "string[%u]" % size, self)
                    self._chunks_dict[identifier][5] = None
                    self._chunks_dict[identifier][6] = {}
                    self.updateChunkDisplay(identifier)
                    return self._createInstance(identifier)
        self._stream.seek(oldpos)
        return chunk

    def getChunk(self, identifier):
        if identifier not in self._chunks_dict:
            return None
        if identifier not in self._chunks_cache:
            chunk = self._createInstance(identifier) 
            self._chunks_cache[chunk.id] = chunk 
            return chunk
        else:
            return self._chunks_cache[identifier]

    def __getitem__(self, identifier):
        assert identifier in self._chunks_dict
        chunk = self.getChunk(identifier)
        if isinstance(chunk.__class__, FilterChunk):
            return chunk.getFilter()
        else:
            return chunk.value

class DeflateFilter(OnDemandFilter):
    def __init__(self, stream, parent, bz_stream, size, filter, *args):
        OnDemandFilter.__init__(self, "deflate", "Deflate", bz_stream, parent)
        self._addr = stream.tell()
        self.read("data", "Data", [filter]+[i for i in args])
        self._compressed_size = size

    def getSize(self):
        return self._compressed_size
