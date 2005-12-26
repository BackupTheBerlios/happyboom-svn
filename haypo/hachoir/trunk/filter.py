"""
Base class for all splitter filters.
"""

import struct, re, sys, string, types
import config
import ui.ui as ui
from chunk import Chunk, FormatChunk, FilterChunk, StringChunk
from error import error
from tools import getBacktrace
from format import getFormatSize

class BasicFilter:
    def __init__(self, id, description, stream, parent, addr):
        self._id = id
        self._description = description
        self._stream = stream
        self._parent = parent
        self._addr = addr 
        self._chunks_counter = {}
        self._chunks_dict = {}

    def updateParent(self, chunk): pass
    def getId(self): return self._id
    def setId(self, id): self._id = id
    def getDescription(self): return self._description
    def setDescription(self, description): self._description = description
    def getAddr(self): return self._addr
    def setAddr(self, addr): self._addr = addr
    def getParent(self): return self._parent
    def getStream(self): return self._stream
    def purgeCache(self): pass
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
            m = Filter.regex_chunk_uniq_id.match(id)
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

    # --- Pure virtual methods -----------
    def getSize(self): assert False
    def __getitem__(self, chunk_id): assert False
    def getChunk(self, chunk_id): assert False
    def display(self): assert False

class OnDemandFilter(BasicFilter):
    def __init__(self, id, description, stream, parent):
        BasicFilter.__init__(self, id, description, stream, parent, stream.tell())
        self._size = 0
        self._chunks = []
        self._chunks_cache = {}
    
    def updateChunkDescription(self, id, desc):
        pos = self._chunks.index(id)
        assert pos != -1
        self._chunks_dict[id][1] = desc

        info = self.displayChunkInfo(id)
        ui.window.update_table(self, pos, *info)

    def purgeCache(self):
        if len(self._chunks_cache) != 0:
            print "Purge cache: destroy %s chunks" % len(self._chunks_cache)
        self._chunks_cache = {}
        
    def doReadChild(self, id, description, filter_class, *args):
        id = self._readStreamChild(id, description, self._stream, None, filter_class, *args)
        return self.getChunk(id)
        
    def readChild(self, id, description, filter_class, *args): 
        return self._readStreamChild(id, description, self._stream, None, filter_class, *args)
        
    def readSizedChild(self, id, description, size, filter_class, *args): 
        return self._readStreamChild(id, description, self._stream, size, filter_class, *args)
        
    def readStreamChild(self, id, description, filter_stream, filter_class, *args): 
        return self._readStreamChild(id, description, filter_stream, None, filter_class, *args)

    def readSizedStreamChild(self, id, description, size, filter_stream, filter_class, *args): 
        return self._readStreamChild(id, description, filter_stream, size, filter_class, *args)

    def _readStreamChild(self, id, description, filter_stream, size, filter_class, *args): 
        id = self.getUniqChunkId(id)
        addr = self._stream.tell()
        filter_addr = filter_stream.tell()
        
        if size == None:
            filter = filter_class(filter_stream, self, *args)
            description = filter.getDescription()
            filter.setId(id)
            chunk = FilterChunk(id, filter, self, addr)
            size = filter.getSize()
            if config.verbose:
                print "%s: Instanciate filter %s" % (self.getPath(), id)
        else:
            chunk = None

        chunk_info = [id, description, addr, size, \
                (filter_class, filter_stream, filter_addr, args), None, {}]
        self._chunks_dict[id] = chunk_info
        self._chunks.append(id)
        if chunk != None:
            filter.updateParent(chunk)
            self._chunks_cache[id] = chunk
        self._size = self._size + size
        self._stream.seek(addr + size)
        return id

    def doRead(self, id, format, description, post=None):
        id = self.read(id, format, description, post)
        return self.getChunk(id)

    def read(self, id, format, description, post=None):
        id = self.getUniqChunkId(id)
        size = getFormatSize(format)
        addr = self._stream.tell()
        chunk_info = [id, description, addr, size, \
                (FormatChunk, id, description, self._stream, addr, format, self,), post, {}]
        self._chunks_dict[id] = chunk_info
        self._chunks.append(id)
        self._stream.seek(size, 1)
        self._size = self._size + size
        return id

    def readString(self, id, format, description, post=None, strip=None):
        id = self.getUniqChunkId(id)
        addr = self._stream.tell()

        chunk = StringChunk(id, description, self._stream, format, self, strip=strip)
        size = chunk.size

        chunk_info = [id, description, addr, size, \
                (StringChunk, id, description, self._stream, format, self,), post, {"strip": strip}]
        self._chunks_dict[id] = chunk_info
        self._chunks.append(id)
        self._chunks_cache[id] = chunk
#        self._stream.seek(size, 1)
        self._size = self._size + size
        return id

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
            self._chunks_cache[id] = self._createInstance(id) 
        return self._chunks_cache[id]

    def __getitem__(self, id):
        assert id in self._chunks_dict
        chunk = self.getChunk(id)
        if isinstance(chunk.__class__, FilterChunk):
            return chunk.getFilter()
        else:
            return chunk.value

class Filter(BasicFilter):
    regex_chunk_uniq_id = re.compile("^(.*?)([0-9]+)$")

    def __init__(self, id, description, stream, parent):
        BasicFilter.__init__(self, id, description, stream, parent, stream.tell())
        self.filter_chunk = None 
        self._chunks = []
        self._chunks_dict = {}
        self._cache_valid = False
        self._cache_size = None

    def __getitem__(self, chunk_id):
        return self.getChunk(chunk_id).getValue()

    def clone(self, addr=None):
        if self.__class__ == Filter:
            return None
        if addr == None:
            addr = self.getAddr()
        self.getStream().seek(addr)
        try:
            new = self.__class__(self.getStream(), self.getParent())
        except:
            error("Error while clone class of type %s!" % self.__class__)
            raise
        new.filter_chunk = self.filter_chunk
        return new

    def _deleteChunk(self, pos):
        self._cache_valid = False
        chunk = self._chunks[pos]
        if chunk.id in self._chunks_dict:
            del self._chunks_dict[chunk.id]
        if hasattr(self, chunk.id):
            delattr(self, chunk.id)        
        del self._chunks[pos]

    def deleteChunk(self, chunk):
        if len(self._chunks) < 2:
            error("Can't not delete the chunk %s (there is only one chunk)." % chunk.id)
            return            
        chunk_size = chunk.size
        pos = self._chunks.index(chunk)
        self._deleteChunk(pos)
        # Delete last chunk of a sub filter? It true, truncate the sub filter
        truncate = (self.getParent() != None and pos == len(self._chunks))
        self.rescanFromPos(pos, -chunk_size, truncate=truncate)
        self.redisplay()

    def getChunks(self):
        return self._chunks

    def updateChunkId(self, chunk, new_id):
        if chunk.id == new_id: return
        if new_id in self._chunks_dict or hasattr(self, new_id):
            raise Exception("Chunk identifier \"%s\" already exist!" % new_id)
        if hasattr(self, chunk.id):
            value = getattr(self, chunk.id)
            delattr(self, chunk.id)
            setattr(self, new_id, value)
        if chunk.id in self._chunks_dict:
            del self._chunks_dict[chunk.id]
        self._chunks_dict[new_id] = chunk
        
    def addRawChunk(self, prev_chunk, id, size, description):
        if prev_chunk != None:
            addr = prev_chunk.addr + prev_chunk.size
            chunk_pos = self._chunks.index(prev_chunk)+1
        else:
            addr = self.getAddr()
            chunk_pos = len(self._chunks)
        chunk = FormatChunk(id, description, self.getStream(), addr, "!%ss" % size, self)
        self.appendChunk(chunk, position=chunk_pos)

    def rescan(self, from_chunk, diff_size, new_id=None, new_description=None, truncate=False):
        if from_chunk != None:
            start = self._chunks.index(from_chunk)+1
        else:
            start = 0
        self.rescanFromPos(start, diff_size, new_id, new_description, truncate)
            
    def _rescanUpdateSize(self, diff_size, new_id=None, new_description=None):
        # Only process diff_size < 0
        if 0 <= diff_size: return

        # Get last chunk
        if 0 < len(self._chunks):
            prev_chunk = self._chunks[-1]
        else:
            prev_chunk = None
        
        if prev_chunk != None and issubclass(prev_chunk.__class__, FormatChunk):
            # If last chunk is a FormatChunk, update it's size
            size = prev_chunk.size - diff_size
            prev_chunk.convertToStringSize(size)
            self._cache_valid = False
        else:
            # Get id
            if new_id != None:
                id = new_id
            else:
                id = "raw"
            id = self.getUniqChunkId(id)

            # Get description
            if new_description != None:
                description = new_description
            else:
                description = ""

            # Get size
            if self.getParent() == None:
                size = self._stream.getSize() - self.getSize() 
            else:
                size = -diff_size
            self.addRawChunk(prev_chunk, id, size, description)

    def _rescanUpdateChunks(self, start, prev_chunk):
        self._cache_valid = False
        pos = start
        try:
            for chunk in self._chunks[start:]:
                # Update start address
                if prev_chunk != None:
                    chunk.addr = prev_chunk.addr + prev_chunk.size
                else:
                    chunk.addr = self.getAddr()
                chunk.update()
                prev_chunk = chunk
                pos = pos + 1
        except Exception, msg:
            error("Exception while updating a filter:\n%s\n%s" \
                % (msg,getBacktrace()))
            iter = len(self._chunks)-1
            while pos<=iter:
                self._deleteChunk(iter)
                iter = iter - 1

    def rescanFromPos(self, start, diff_size, new_id=None, new_description=None, truncate=False):
        assert 0<=start and start <= len(self._chunks)
        self._cache_valid = False
        if 0<start:
            prev_chunk = self._chunks[start-1]
        else:
            prev_chunk = None

        # Update chunks address
        old_size = self.getSize()
        self._rescanUpdateChunks(start, prev_chunk)
        diff_size = diff_size + (self.getSize() - old_size)

        # Update last chunk size if needed
        if not truncate:
            self._rescanUpdateSize(diff_size, new_id, new_description)
            diff_size = 0
               
        if self.getParent() != None:
            self.getParent().rescan(self.filter_chunk, diff_size)

    def getLastPos(self):
        if len(self._array) == 0: return self.getAddr()
        last_chunk = self._array[-1]
        return last_chunk.addr + last_chunk.size

    def getSize(self):
        if not self._cache_valid:
            self._cache_valid = True
            size = 0
            for chunk in self._chunks:
                size = size + chunk.size
            self._cache_size = size
        return self._cache_size

    def addString(self, str_type, before_chunk):
        if before_chunk != None:
            pos = self._chunks.index(before_chunk)
            addr = before_chunk.addr
        else:
            pos = len(self._chunks)
            addr = self.getAddr()
        stream = self.getStream()
        stream.seek(addr)
        id = self.getUniqChunkId("str")
        str_chunk = StringChunk(id, "String", stream, str_type, self)
        self.appendChunk(str_chunk, position=pos)
        str_chunk.postProcess()
        before_chunk.addr = before_chunk.addr + str_chunk.size
        before_chunk.convertToStringSize(before_chunk.size - str_chunk.size)
        self.redisplay()
        return str_chunk

    def updateParent(self, chunk):
        pass

    def getChunk(self, chunk_id):
        chunk = self._chunks_dict.get(chunk_id, None)
        if chunk == None:
            raise Exception("Filter \"%s\" has no chunk with id \"%s\"." \
                % (self.getId(), chunk_id))
        return chunk

    def displayChunk(self, chunk):
        type = chunk.getSmallFormat()
        if isinstance(chunk, FilterChunk):
            addr = chunk.parent_addr
        else:
            addr = chunk.addr
        ui.window.add_table(None, addr, chunk.size, type, chunk.id, chunk.description, chunk.getDisplayData())

    def redisplay(self):  
        self.display()
    
    def display(self):  
        ui.window.enableParentButton(self.getParent() != None)
            
        # Update table
        ui.window.clear_table()
        for chunk in self._chunks:
            self.displayChunk(chunk)

    def readField(self, id, description, delimiter):
        lg = self._stream.searchLength(delimiter, False)
        if lg == -1:
            raise Exception("Delimiter \"%s\" not found for %s (%s)!" % (delimiter, id, description))
        self.read(id, "!%us" % lg, description) 
        self.read(id+"_delimiter", "!%us" % len(delimiter), "Delimiter of %s" % id) 

    def searchEol(self, eol):
        lg = self._stream.searchLength(eol, True)
        if lg == -1:
            return self._stream.getLastPos() - self._stream.tell()
        else:
            return lg

    def readLine(self, id, description, eol="\n", fails_if_not_found=False, can_truncate=False):
        lg = self.searchEol(eol)
        self.read(id, "!%us" % lg, description, truncate=can_truncate)
        line = getattr(self, id)
        setattr(self, id, line[:-len(eol)])

    def updateFormatChunk(self, chunk):
        if chunk.id == None: return
        self._cache_valid = False
        data = chunk.getValue(config.max_string_length)
        setattr(self, chunk.id, data)       

    def appendChunk(self, chunk, position=None):
        self._cache_valid = False
        if position == None:
            self._chunks.append(chunk)
        else:
            self._chunks.insert(position, chunk)
        self._chunks_dict[chunk.id] = chunk

    def readLimitedChild(self, id, size, filter_class, *args):
        start = self._stream.tell()
        limited = self._stream.createLimited(start, size)
        chunk = self.readStreamChild(id, limited, filter_class, *args)
        assert self._stream.tell() == (start+size)
        return chunk
        
    def readStreamChild(self, id, stream, filter_class, *args): 
        id = self.getUniqChunkId(id)
        oldpos = self._stream.tell()
        filter = filter_class(stream, self, *args)
        filter.setId(id)
        chunk = self.addFilter(id, filter, oldpos)
        chunk.postProcess()
        self._stream.seek(oldpos + chunk.size)
        return chunk
        
    def readChild(self, id, filter_class, *args): 
        return self.readStreamChild(id, self._stream, filter_class, *args)
    
    def addFilter(self, id, filter, addr): 
        chunk = FilterChunk(id, filter, self, addr)
        self.appendChunk(chunk)
        filter.updateParent(chunk)
        return chunk

    def readArray(self, id, entry_class, description, end_func): 
        """
        end_func: def isEnd(stream, array, last_filter)
        """
        addr = self._stream.tell()
        filter = ArrayFilter(id, description, self._stream, self, entry_class, end_func)
        chunk = self.addFilter(id, filter, addr)
        chunk.postProcess()
        return chunk
    
    def readString(self, id, format, description, post=None, strip=None):
        """ Returns chunk """
        id = self.getUniqChunkId(id)
        chunk = StringChunk(id, description, self._stream, format, self, strip=strip)
        self.appendChunk(chunk)
        self._stream.seek(chunk.addr + chunk.size)
        chunk.post_process = post
        chunk.postProcess()
        return chunk
    
    def read(self, id, format, description, post=None):
        """ Returns chunk """
        id = self.getUniqChunkId(id)
        chunk = FormatChunk(id, description, self._stream, self._stream.tell(), format, self)
        self.appendChunk(chunk)
        self._stream.seek(chunk.addr + chunk.size)
        chunk.post_process = post
        chunk.postProcess()
        return chunk

    def __str__(self):
        return "Filter(%s) <id=%s, description=%s>" % \
            (self.__class__, self.getId(), self.getDescription())

    def addNewFilter(self, chunk, id, size, desc):
        chunk.setFormat("%us" % size, "split", id, desc)
        self.convertChunkToFilter(chunk)

    def convertFilterToChunk(self, chunk):
        # Create new format chunk
        filter = chunk.getFilter()
        id = self.getUniqChunkId(filter.getId())
        new_chunk = FormatChunk(id, filter.getDescription(), filter.getStream(), filter.getAddr(), "!%us" % filter.getSize(), self)

        # Delete old chunk
        if chunk.id in self._chunks_dict:
            del self._chunks_dict[chunk.id]
        if hasattr(self, chunk.id):
            delattr(self, chunk.id)

        # Assign new chunk
        pos = self._chunks.index(chunk)
        self._chunks[pos] = new_chunk
        self._chunks_dict[id] = new_chunk
        setattr(self, id, chunk.getValue(40))
        self.redisplay()
        return new_chunk 

    def convertChunkToFilter(self, chunk):
        # Create new filter
        stream = self.getStream()
        stream.seek(chunk.addr)
        filter = Filter(chunk.id, chunk.description, stream, self)
        chunk.setParent(filter)
        filter.appendChunk(chunk)
        
        # Create new chunk and add it into self 
        new_chunk = FilterChunk(chunk.id, filter, self, chunk.addr)
        pos = self._chunks.index(chunk)
        self._chunks[pos] = new_chunk
        self._chunks_dict[chunk.id] = new_chunk
        self.redisplay()
        return filter

class ArrayFilter(Filter):
    def __init__(self, id, description, stream, parent, entry_class, end_func):
        Filter.__init__(self, id, description, stream, parent)
        self._entry_class = entry_class
        self._end_func = end_func
        self._read()

    def _read(self):
        self._array = []
        nb = 0
        last_filter = None
        while not self._end_func(self._stream, self._array, last_filter):
            chunk_id = "%s[%u]" % (self.getId(), nb)
            addr = self._stream.tell()
            filter = self._entry_class(self._stream, self)
            filter.setId(chunk_id)
            nb = nb + 1
            chunk = FilterChunk(chunk_id, filter, self, addr)
            self._array.append( chunk )
            self.appendChunk(chunk)
            last_filter = filter

        for chunk in self._array:
            chunk.getFilter().updateParent(chunk)
        if 1<nb:
            self.setDescription( "%s (%s items)" % (self.getDescription(), nb))
        else:
            self.setDescription( "%s (%s item)" % (self.getDescription(), nb))

    def getArray(self):
        return self._array
    
    def _deleteChunk(self, pos):
        Filter._deleteChunk(self, pos)
        if pos < len(self._array):
            del self._array[pos]

    def update(self):
        self._cache_valid = False
        prev_chunk = None
        pos = 0
        try:
            for chunk in self._array:
                if prev_chunk != None:
                    chunk.addr = prev_chunk.addr + prev_chunk.size
                else:
                    chunk.addr = self.getAddr()
                chunk.update()
                prev_chunk = chunk
                pos = pos + 1
        except Exception, msg:
            error("Exception while updating an ArrayFilter:\n%s" % msg)
            chunk = self._array[pos]
            addr = chunk.addr
            size = self.getLastPos() - addr
            del self._array[pos:]
            if size != 0:
                chunk = FormatChunk("raw", "Raw data", chunk.getStream(), addr, "!%us" % size, self)
                self._array.append(chunk)

    def __len__(self):
        return len(self._array)

    def __getitem__(self, index):
        return self._array[index]

    def clone(self, addr=None):
        if addr == None:
            addr = self.getAddr()
        self.getStream().seek(addr)
        new = ArrayFilter( self.getId(), self.getDescription(), \
            self.getStream(), self.getParent(), self._entry_class, self._end_func)
        new.filter_chunk = self.filter_chunk
        return new

class DeflateFilter(Filter):
    def __init__(self, stream, parent, bz_stream, size, filter, *args):
        Filter.__init__(self, "deflate", "Deflate", bz_stream, parent)
        self._addr = stream.tell()
        self.readChild("data", filter, *args)
        self._compressed_size = size

    def getSize(self):
        return self._compressed_size
