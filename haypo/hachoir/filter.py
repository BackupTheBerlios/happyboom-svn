"""
Base class for all splitter filters.
"""

import struct
import re, sys
import string
import types
import ui
from chunk import Chunk, FormatChunk, ArrayChunk, FilterChunk
    
class Filter:
    def __init__(self, id, description, stream, parent=None):
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
        self.indent = " " * ((self.depth-1)*2)
        self.child_indent = " " * (self.depth*2)
        self.table_item = None
        self.__last_child_stream_pos = None 
        self._chunks = []
        self._chunks_dict = {}
        self._addr = self._stream.tell()

    def getAddr(self):
        return self._addr

    def getSize(self):
        size = 0
        for chunk in self._chunks:
            size = size + chunk.size
        return size

    def updateParent(self, parent, chunk):
        pass

    def getChunk(self, chunk_id):
        return self._chunks_dict.get(chunk_id, None)

    def displayChunk(self, chunk):
        type = chunk.__class__
        if issubclass(type, FormatChunk):
            type = chunk.getFormat()
        elif issubclass(type, FilterChunk):
            type = chunk.getFilter().id
        ui.ui.add_table(self.table_parent, chunk.addr, chunk.size, type, chunk.id, chunk.description, chunk.getDisplayData())

    def display(self):  
        # Update parent button
        ui.ui.enableParentButton(self.getParent() != None)
        
        # Update status bar
        text = ""
        current = self
        while current != None:
            if text != "": text = " > " + text
            text = current.id + text
            current = current.getParent()
        ui.ui.updateStatusBar("%s: %s" % (text, self.description))
            
        # Update table
        ui.ui.clear_table()
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

    def _appendChunk(self, chunk, can_truncate=False):
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
        chunk = FilterChunk(id, filter.description, self._stream, filter)
        self._appendChunk(chunk)
        filter.updateParent(self, chunk)
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
            chunk = FilterChunk(chunk_id, filter.description, self._stream, filter)
            array.append( chunk )
            last_filter = filter

        for chunk in array:
            chunk.getFilter().updateParent(self, chunk)
        self._stream.seek(array_chunk.addr + array_chunk.size)
    
    def read(self, id, format, description, can_truncate=True):
        """ Returns chunk """
#        if self.depth <= display_filter_actions and 0<size:
#            chunk_data.output(self.indent)
#        if can_truncate:
#            data = chunk_data.getData(60)
#        else:
#            data = chunk_data.getData(None)
        chunk = FormatChunk(id, description, self._stream, self._stream.tell(), format, self)
        self._stream.seek(chunk.size, 1)
        self._appendChunk(chunk, can_truncate)
        self._stream.seek(chunk.addr + chunk.size)
        return chunk

    def __str__(self):
        return "Filter(%s) <id=%s, description=%s>" % \
            (self.__class__, self.id, self.description)

    def getParent(self):
        return self._parent

display_filter_actions = 1
