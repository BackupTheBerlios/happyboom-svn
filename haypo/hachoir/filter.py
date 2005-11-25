"""
Base class for all splitter filters.
"""

import struct
import re, sys
import string
import types
import ui.ui as ui
from chunk import Chunk, FormatChunk, FilterChunk, StringChunk
from format import splitFormat    
from error import error
from tools import getBacktrace

class Filter:
    def __init__(self, id, description, stream, parent):
        self._id = id
        self._description = description
        self._stream = stream
        self._parent = parent
        if self._parent:
            self.depth = self._parent.depth + 1
        else:
            self.depth = 1
        self.filter_chunk = None 
        self._chunks = []
        self._chunks_dict = {}
        self._addr = self._stream.tell()

    def clone(self):
        if self.__class__ == Filter:
            return None
        self.getStream().seek(self.getAddr())
        try:
            new = self.__class__(self.getStream(), self.getParent())
        except:
            error("Error while clone class of type %s!" % self.__class__)
            raise
        new.filter_chunk = self.filter_chunk
        return new

    def getId(self): return self._id
    def setId(self, id): self._id = id
    def getDescription(self): return self._description
    def setDescription(self, description): self._description = description

    def _deleteChunk(self, pos):
        chunk = self._chunks[pos]
        if chunk.id in self._chunks_dict:
            del self._chunks_dict[chunk.id]
        if hasattr(self, chunk.id):
            delattr(self, chunk.id)        
        del self._chunks[pos]

    def deleteChunk(self, chunk):
        if len(self._chunks) < 2:
            error("Can't not the chunk %s (there is only one chunk)." % chunk.id)
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

    def getUniqChunkId(self, id):
        if id not in self._chunks_dict: return id
        m = re.compile("^(.*)([0-9]+)$").match(id)
        if m != None:
            root = m.group(1)
            uniq = int(m.group(2))+1
        else:
            root = id
            uniq = 2
        new_id = "%s%u" % (root, uniq)
        while new_id in self._chunks_dict:
            uniq = uniq+1
            new_id = "%s%u" % (root, uniq)
        return new_id 

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
        self._appendChunk(chunk, can_truncate=True, position=chunk_pos)

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
            format = splitFormat(prev_chunk.getFormat())
            if self.getParent() == None:
                if format[1] != "{@end@}":
                    prev_chunk.convertToStringSize("{@end@}")
            else:
                size = prev_chunk.size - diff_size
                prev_chunk.convertToStringSize(size)
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
                size = "{@end@}"
            else:
                size = -diff_size
            self.addRawChunk(prev_chunk, id, size, description)

    def _rescanUpdateChunks(self, start, prev_chunk):
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

    def getAddr(self):
        return self._addr

    def setAddr(self, addr):
        self._addr = addr

    def getLastPos(self):
        if len(self._array) == 0: return self.getAddr()
        last_chunk = self._array[-1]
        return last_chunk.addr + last_chunk.size

    def getSize(self):
        size = 0
        for chunk in self._chunks:
            size = size + chunk.size
        return size

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
        self._appendChunk(str_chunk, can_truncate=True, position=pos)
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
        type = chunk.getFormat()
        ui.window.add_table(None, chunk.addr, chunk.size, type, chunk.id, chunk.description, chunk.getDisplayData())

    def redisplay(self):  
        self.display()
    
    def updateStatusBar(self):
        text = ""
        current = self
        while current != None:
            if text != "": text = " > " + text
            text = current.getId() + text
            current = current.getParent()
        ui.window.updateStatusBar("%s: %s (size=%s)" % (text, self.getDescription(), self.getSize()))

    def display(self):  
        ui.window.enableParentButton(self.getParent() != None)
        self.updateStatusBar()
            
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
        data = chunk.getValue(40)
        setattr(self, chunk.id, data)       

    def _appendChunk(self, chunk, can_truncate=False, position=None):
        if position != None:
            self._chunks.insert(position, chunk)
        else:
            self._chunks.append(chunk)
        id = chunk.id
        assert id != None
        m = re.compile(r"^([^[]+)\[\]$").match(id)
        if m != None:
            id = m.group(1)
            if hasattr(self, id):
                array = getattr(self, id)
            else:
                array = []
                setattr(self, id, array)
            assert type(array) == types.ListType
            chunk.id = "%s[%u]" % (id, len(array))
            array.append(chunk)
            if id not in self._chunks_dict:
                self._chunks_dict[id] = array 
        else:
            if hasattr(self, id):
                raise Exception("Chunk identifier \"%s\" already exist!" % id)
            if can_truncate:
                data = chunk.getValue(40)
            else:
                data = chunk.getValue()
            setattr(self, id, data)
            self._chunks_dict[id] = chunk

    def readLimitedChild(self, id, size, filter_class, *args):
        start = self._stream.tell()
        limited = self._stream.createLimited(start, size)
        filter = filter_class(limited, self, *args)
        chunk = self.addFilter(id, filter)
        chunk.postProcess()
        self._stream.seek(start+size)
        return chunk
        
    def readChild(self, id, filter_class, *args): 
        filter = filter_class(self._stream, self, *args)
        chunk = self.addFilter(id, filter)
        chunk.postProcess()
        return chunk
    
    def addFilter(self, id, filter): 
        chunk = FilterChunk(id, filter, self)
        self._appendChunk(chunk)
        filter.updateParent(chunk)
        self._stream.seek(chunk.addr + chunk.size)
        return chunk

    def readArray(self, id, entry_class, description, end_func): 
        """
        end_func: def isEnd(stream, array, last_filter)

        """
        filter = ArrayFilter(id, description, self._stream, self, entry_class, end_func)
        chunk = self.addFilter(id, filter)
        chunk.postProcess()
        return chunk
    
    def readString(self, id, format, description, post=None):
        """ Returns chunk """
        chunk = StringChunk(id, description, self._stream, format, self)
        self._appendChunk(chunk)
        self._stream.seek(chunk.addr + chunk.size)
        chunk.post_process = post
        chunk.postProcess()
        return chunk
    
    def read(self, id, format, description, post=None, truncate=False):
        """ Returns chunk """
        chunk = FormatChunk(id, description, self._stream, self._stream.tell(), format, self)
        self._appendChunk(chunk, can_truncate=truncate)
        self._stream.seek(chunk.addr + chunk.size)
        chunk.post_process = post
        chunk.postProcess()
        return chunk

    def __str__(self):
        return "Filter(%s) <id=%s, description=%s>" % \
            (self.__class__, self.getId(), self.getDescription())

    def addNewFilter(self, chunk, id, size, desc):
        chunk.setFormat("!%ss" % size, "split", id, desc)
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
        filter._appendChunk(chunk, can_truncate=True)
        
        # Create new chunk and add it into self 
        new_chunk = FilterChunk(chunk.id, filter, self)
        pos = self._chunks.index(chunk)
        self._chunks[pos] = new_chunk
        self._chunks_dict[chunk.id] = new_chunk
        self.redisplay()
        return filter

    def getParent(self):
        return self._parent

    def getStream(self):
        return self._stream

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
            filter = self._entry_class(self._stream, self)
            chunk_id = "%s[%u]" % (self.getId(), nb)
            nb = nb + 1
            chunk = FilterChunk(chunk_id, filter, self)
            self._array.append( chunk )
            self._appendChunk(chunk)
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

    def clone(self):
        self.getStream().seek(self.getAddr())
        new = ArrayFilter( self.getId(), self.getDescription(), \
            self.getStream(), self.getParent(), self._entry_class, self._end_func)
        new.filter_chunk = self.filter_chunk
        return new
