"""
Base class for all splitter filters.
"""

import struct
import re, sys
import string
import types
import ui
from chunk import Chunk, FormatChunk, ArrayChunk, FilterChunk
from format import splitFormat    

class Filter:
    def __init__(self, id, description, stream, parent):
        self.id = id
        self.description = description
        self._sub_struct = {}
        self._stream = stream
        self._parent = parent
        if self._parent:
            self.depth = self._parent.depth + 1
            self.table_parent = self._parent.table_item
        else:
            self.depth = 1
            self.table_item = None
            self.table_parent = None 
        self.filter_chunk = None 
        self.indent = " " * ((self.depth-1)*2)
        self.child_indent = " " * (self.depth*2)
        self.table_item = None
        self.__last_child_stream_pos = None 
        self._chunks = []
        self._chunks_dict = {}
        self._addr = self._stream.tell()

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
        addr = prev_chunk.addr + prev_chunk.size
        chunk = FormatChunk(id, description, self.getStream(), addr, "!%ss" % size, self)
        chunk_pos = self._chunks.index(prev_chunk)+1
        self._appendChunk(chunk, can_truncate=True, position=chunk_pos)

    def rescan(self, from_chunk, diff_size, new_id=None, new_description=None):
        if from_chunk != None:
            start = self._chunks.index(from_chunk)+1
            prev_chunk = from_chunk
        else:
            start = 0
            prev_chunk = None
        if start == len(self._chunks):
            print "Here"
            if diff_size < 0:
                if new_id != None:
                    id = new_id
                else:
                    id = from_chunk.id
                id = self.getUniqChunkId(id)
                if new_description != None:
                    description = new_description
                else:
                    description = from_chunk.description
                self.addRawChunk(from_chunk, id, "{@end@}", description)
            return

        pos = start
        try:
            for chunk in self._chunks[start:]:
                # Update start address
                if prev_chunk != None:
                    chunk.addr = prev_chunk.addr + prev_chunk.size
                else:
                    chunk.addr = self.addr
                chunk.update()
                if pos == len(self._chunks)-1 and issubclass(chunk.__class__, FormatChunk):
                    format = splitFormat(chunk.getFormat())
                    if format[1] != "{@end@}":
                        chunk.convertToStringSize("{@end@}")
                prev_chunk = chunk
                pos = pos + 1
        except Exception, msg:
            print "Exception while updating a filter:\n%s" % msg
            chunk = self._chunks[pos]
            size = self._stream.getSize() - chunk.addr
            del self._chunks[pos:]
            if size != 0:
                chunk = FormatChunk("raw", "Raw data", chunk.getStream(), chunk.addr, "!%us" % size, self)
                self._appendChunk(chunk)

    def getAddr(self):
        return self._addr

    def getSize(self):
        size = 0
        for chunk in self._chunks:
            size = size + chunk.size
        return size

    def updateParent(self, chunk):
        pass

    def getChunk(self, chunk_id):
        m = re.compile(r"^([^[]+)\[([0-9]+)\]$").match(chunk_id)
        if m != None:
            array = self._chunks_dict.get(m.group(1), None)
            if array == None: return None
            return array[int(m.group(2))]
        else:
            return self._chunks_dict.get(chunk_id, None)

    def displayChunk(self, chunk):
        type = chunk.__class__
        if issubclass(type, FormatChunk):
            type = chunk.getFormat()
        elif issubclass(type, FilterChunk):
            type = chunk.getFilter().id
        ui.window.add_table(self.table_parent, chunk.addr, chunk.size, type, chunk.id, chunk.description, chunk.getDisplayData())

    def redisplay(self):  
        self.display()
    
    def updateStatusBar(self):
        text = ""
        current = self
        while current != None:
            if text != "": text = " > " + text
            text = current.id + text
            current = current.getParent()
        ui.window.updateStatusBar("%s: %s" % (text, self.description))

    def display(self):  
        ui.window.enableParentButton(self.getParent() != None)
        self.updateStatusBar()
            
        # Update table
        ui.window.clear_table()
        for chunk in self._chunks:
            if issubclass(chunk.__class__, ArrayChunk):
                for subchunk in chunk:
                    self.displayChunk(subchunk)
            else:
                self.displayChunk(chunk)

    def __isStrPrintable(self, str):
        """
        Can a string be printed on the screen?
        """
        for c in str:
            if c not in string.printable: return False
        return True

    def readField(self, id, description, delimiter):
        lg = self._stream.searchLength(delimiter, False)
        if lg == -1:
            raise Exception("Delimiter \"%s\" not found for %s (%s)!" % (delimiter, id, description))
        self.read(id, "!%us" % lg, description) 
        self.read(None, "!%us" % len(delimiter), "Delimiter of %s" % id) 

    def searchEol(self, eol):
        lg = self._stream.searchLength(eol, True)
        if lg == -1:
            return self._stream.getLastPos() - self._stream.tell()
        else:
            return lg

    def readLine(self, id, description, eol="\n", fails_if_not_found=False, can_truncate=False):
        lg = self.searchEol(eol)
        self.read(id, "!%us" % lg, description, can_truncate)
        line = getattr(self, id)
        setattr(self, id, line[:-len(eol)])

    def _appendChunk(self, chunk, can_truncate=False, position=None):
        if position != None:
            self._chunks.insert(position, chunk)
        else:
            self._chunks.append(chunk)
        id = chunk.id
        if id != None:
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
                    data = chunk.getData(40)
                else:
                    data = chunk.getData()
                setattr(self, id, data)
                self._chunks_dict[id] = chunk

    def readChild(self, id, filter_class, description): 
        filter = filter_class(self._stream, self)
        chunk = FilterChunk(id, filter, self)
        self._appendChunk(chunk)
        filter.updateParent(chunk)
        self._stream.seek(chunk.addr + chunk.size)

    def readArray(self, id, filter_class, description, end_func): 
        array = []
        array_chunk = ArrayChunk(id, description, self._stream, array, self)
        self._appendChunk(array_chunk)

        nb = 0
        last_filter = None
        while not end_func(self._stream, array, last_filter):
            filter = filter_class(self._stream, self)
            chunk_id = "%s[%u]" % (id, nb)
            nb = nb + 1
            chunk = FilterChunk(chunk_id, filter, self)
            array.append( chunk )
            last_filter = filter

        for chunk in array:
            chunk.getFilter().updateParent(chunk)
        self._stream.seek(array_chunk.addr + array_chunk.size)
    
    def read(self, id, format, description, can_truncate=True):
        """ Returns chunk """
#        print "* Read chunk %s: format %s" % (id, format)
        chunk = FormatChunk(id, description, self._stream, self._stream.tell(), format, self)
        self._stream.seek(chunk.size, 1)
        self._appendChunk(chunk, can_truncate)
        self._stream.seek(chunk.addr + chunk.size)
        return chunk

    def __str__(self):
        return "Filter(%s) <id=%s, description=%s>" % \
            (self.__class__, self.id, self.description)

    def addNewFilter(self, chunk, id, size, desc):
        chunk.setFormat("!%us" % size, "split", id, desc)

        stream = self.getStream()
        stream.seek(chunk.addr)
        filter = Filter(id, desc, stream, self)
        filter._appendChunk(chunk)
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
