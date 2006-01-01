"""
Base class for all splitter filters.
"""

import struct, re, sys, string, types
import config
import ui.ui as ui
from chunk import Chunk, FormatChunk, FilterChunk, StringChunk, BitsChunk
from error import error
from format import getFormatSize, splitFormat
from cache import Cache

class BasicFilter(object):
    regex_chunk_uniq_id = re.compile("^(.*?)([0-9]+)$")

    def __init__(self, id, description, stream, parent, addr, endian):
        self._id = id
        self._description = description
        self._stream = stream
        self._parent = parent
        self._addr = addr 
        self._chunks_counter = {}
        self._chunks_dict = {}
        self._endian = endian
        self.filter_chunk = None

    def getStaticSize(stream, args):
        return None
    getStaticSize = staticmethod(getStaticSize)

    def updateParent(self, chunk): pass
    def getId(self): return self._id
    def setId(self, id):
        if self._id == id:
            return
        self._id = id
        if self.filter_chunk != None:
            self.filter_chunk.id = id
    def getDescription(self): return self._description
    def setDescription(self, description): self._description = description
    def getAddr(self): return self._addr
    def getParent(self): return self._parent
    def getStream(self): return self._stream
    def updateChunkId(self, old_id, new_id): pass
    def updateChunkDescription(self, id, desc): pass
    def __len__(self): return len(self._chunks_dict)

    def getPath(self):
        """
        Get path to the filter.
        Example: "grandparent > parent > item"
        """
        text = ""
        current = self
        while current != None:
            if text != "": text = "/" + text
            text = current.getId() + text
            current = current.getParent()
        return "/"+text

    def _getUniqChunkId(self, root, index):
        if root in self._chunks_counter:
            self._chunks_counter[root] = self._chunks_counter[root] + 1
        else:
            self._chunks_counter[root] = index
        return self._chunks_counter[root]

    def getUniqChunkId(self, id):
        # No collision
        if id not in self._chunks_dict and id[-2:] != "[]":
            return id

        # Pattern like "block[]"
        if id[-2:] == "[]":
            root = id[:-2]
            start = 0
            pattern = "%s[%u]"
        else:
            # Manage id collision
            m = BasicFilter.regex_chunk_uniq_id.match(id)
            if m != None:
                root = m.group(1)
                start = int(m.group(2)) + 1
            else:
                root = id
                start = 2
            pattern = "%s%u"
        if root in self._chunks_counter:
            self._chunks_counter[root] = self._chunks_counter[root] + 1
        else:
            self._chunks_counter[root] = start 
        return pattern % (root, self._chunks_counter[root])
        
    def hasChunk(self, id):
        return id in self._chunks_dict

    def _getEndian(self): return self._endian
    endian = property(_getEndian)

    def addPadding(self):
        size = self._stream.getLastPos() - self._stream.tell()
        if size != 0:
            self.read("end", "Raw end", (FormatChunk, "string[%u]" % size))

    # --- Pure virtual methods -----------
    def getSize(self): todoWriteMethod(self, "getSize") 
    def __getitem__(self, chunk_id): todoWriteMethod(self, "__getitem__") 
    def getChunk(self, chunk_id): todoWriteMethod(self, "getChunk")
    def display(self): todoWriteMethod(self, "display")

class OnDemandFilter(BasicFilter, Cache):
    def __init__(self, id, description, stream, parent, endian=None):
        BasicFilter.__init__(self, id, description, stream, parent, stream.tell(), endian)
        Cache.__init__(self, "Filter %s" % id)
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
        info = self.displayChunkInfo(new_id)
        ui.window.update_table(self, pos, *info)

    def updateChunkDescription(self, id, desc):
        pos = self._chunks.index(id)
        assert pos != -1
        self._chunks_dict[id][1] = desc

        if ui.ui != None:
            info = self.displayChunkInfo(id)
            ui.window.update_table(self, pos, *info)

    def purgeCache(self):
        if len(self._chunks_cache) != 0 and config.verbose:
            print "Purge cache: destroy %s chunks" % len(self._chunks_cache)
        self._chunks_cache = {}
        
    def read(self, id, description, info, optionnal={}): 
        chunk_class = info[0]
        id = self.getUniqChunkId(id)
        addr = self._stream.tell()
        if issubclass(chunk_class, BasicFilter):
            filter_stream = optionnal.get("stream", self._stream)
            size = optionnal.get("size", None)
            filter_addr = filter_stream.tell()
            args = info[1:]
            if size == None:
                size = chunk_class.getStaticSize(self._stream, info[1:])
            if size == None:
                filter = chunk_class(filter_stream, self, *args)
                description = filter.getDescription()
                filter.setId(id)
                chunk = FilterChunk(id, filter, self, addr)
                size = filter.getSize()
                if config.verbose:
                    print "%s: Instanciate filter %s" % (self.getPath(), id)
            else:
                chunk = None

            chunk_info = [id, description, addr, size, \
                    (chunk_class, filter_stream, filter_addr, args), None, {}]
            self._chunks_dict[id] = chunk_info
            self._chunks.append(id)
            if chunk != None:
                filter.updateParent(chunk)
                self._chunks_cache[id] = chunk
            self._size = self._size + size
            self._stream.seek(addr + size)
            return id

        else:
            post = optionnal.get("post", None)
            if "post" in optionnal:
                del optionnal["post"]
            if isinstance(info, list):
                args = info[1:]
            else:
                args = [ i for i in info[1:] ]
            instance_info = [info[0], id, description, self._stream]+args+[self]

            size = chunk_class.getStaticSize(self._stream, info[1:])
            if size != None:
                self._stream.seek(size, 1)
            else:
                # Instanciate the chunk
                seek = False
                chunk = info[0] (*instance_info[1:], **optionnal)
                size = chunk.size
                id = chunk.id
                self._chunks_cache[id] = chunk
            chunk_info = [id, description, addr, size, instance_info, post, optionnal]
#            else:       
#                assert chunk_class == StringChunk
#                strip = optionnal.get("strip", None)
#                chunk = chunk_class (id, description, self._stream, info[1:], self, strip=strip)
#                chunk_info = [id, description, addr, size, \
#                        (info[0], id, description, self._stream, info[1:], self,), post, optionnal]
#                self._chunks_cache[id] = chunk
            self._chunks_dict[id] = chunk_info
            self._chunks.append(id)
            self._size = self._size + size
            return id

    def doRead(self, id, description, info, optionnal={}):
        id = self.read(id, description, info, optionnal)
        chunk = self.getChunk(id)
        if isinstance(chunk, FilterChunk):
            return chunk.getFilter()
        else:
            return chunk

    def displayChunkInfo(self, id):
        info = self._chunks_dict[id]
        chunk_class = info[4][0]
        if issubclass(chunk_class, BasicFilter):
            display = "(...)"
            format = chunk_class.__name__
        else:
            chunk = self.getChunk(id)
            display = chunk.getDisplayData()
            format = chunk.getSmallFormat()
        addr = info[2]
        size = info[3]
        return (None, addr, size, format, info[0], info[1], display)

    def display(self):
        ui.window.enableParentButton(self.getParent() != None)
        ui.window.clear_table()
        for id in self._chunks:
            info = self.displayChunkInfo(id)
            if self._chunks_dict[id][4][0] == BitsChunk:
                self.getChunk(id).uiDisplay(ui.window)
            else:
                ui.window.add_table(*info)
 
    def getSize(self): return self._size

    def _createInstance(self, id):
        addr = self._chunks_dict[id][2]
        desc = self._chunks_dict[id][4]
        post = self._chunks_dict[id][5]
        chunks_kw = self._chunks_dict[id][6]
        oldpos = self._stream.tell()
        self._stream.seek(addr)
        if config.verbose:
            print "%s: Instanciate %s (of type %s)" % (self.getPath(), id, desc[0].__name__)
        if not issubclass(desc[0], BasicFilter):
            chunk_class = desc[0]
            chunk_args = desc[1:]
            chunk = chunk_class(*chunk_args, **chunks_kw)
            if post != None:
                chunk.display = post(chunk)
        else:
            filter_stream = desc[1]
            if filter_stream != self._stream:
                filter_stream.seek(desc[2])
            filter = desc[0] (filter_stream, self, *desc[3])
            filter.setId(id)
            chunk = FilterChunk(id, filter, self, addr)
            if filter.getDescription() != desc[1]:
                self.updateChunkDescription(id, filter.getDescription())
            filter.updateParent(chunk)
        self._stream.seek(oldpos)
        return chunk

    def getChunk(self, id):
        if id not in self._chunks_dict:
            return None
        if id not in self._chunks_cache:
            chunk = self._createInstance(id) 
            self._chunks_cache[chunk.id] = chunk 
            return chunk
        else:
            return self._chunks_cache[id]

    def __getitem__(self, id):
        assert id in self._chunks_dict
        chunk = self.getChunk(id)
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
