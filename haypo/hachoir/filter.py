"""
Base class for all splitter filters.
"""

import struct
import re
import sys
import types
import string
import hmi
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

    def getChunk(self, chunk_id):
        return self._chunks_dict.get(chunk_id, None)

    def displayChunk(self, chunk):
        type = chunk.__class__
        if issubclass(type, FormatChunk):
            type = chunk.getFormat()
        elif issubclass(type, FilterChunk):
            type = chunk.getFilter().id
            #type = "(sub)"
        hmi.hmi.add_table(self.table_parent, chunk.addr, chunk.size, type, "HEX", chunk.id, chunk.description, "")

    def display(self):
        hmi.hmi.enableParentButton(self.getParent() != None)
        text = ""
        current = self
        while current != None:
            if text != "": text = " > " + text
            text = current.id + text
            current = current.getParent()
        hmi.hmi.updateStatusBar(text)
            
        hmi.hmi.clear_table()
        for chunk in self._chunks:
            if issubclass(chunk.__class__, ArrayChunk):
                for subchunk in chunk:
                    self.displayChunk(subchunk)
            else:
                self.displayChunk(chunk)

    def __replaceFieldFormat(self, match):
        return str(getattr(self, match.group(1)))

    def openChild(self):
        return
        self.__child_stream_pos = self._stream.tell()
        self.__last_child_stream_pos = None 

    def closeChild(self, text):
        return
        self.__updateChild(self.__last_child_stream_pos, self.table_item)
        if self.table_parent != None:
            self.__updateChild(self.__child_stream_pos, self.table_parent)
        self.table_item = None
        self.__last_child_stream_pos = None
        if display_filter_actions != self.depth: return
        size = self._stream.tell() - self.__child_stream_pos
        sys.stdout.write("%s<%s (%u bytes)>\n" % (self.indent, text, size))

    def __updateChild(self, pos, table):
        if pos == None or table == None: return False
        size = self._stream.tell() - pos
        hmi.hmi.set_table_value(table, 1, size) 
        return True

    def updateChildTitle(self, text):
        return
        hmi.hmi.set_table_value(self.table_item, 4, text) 

    def updateChildComment(self, comment):
        return
        hmi.hmi.set_table_value(self.table_item, 5, comment) 

    def newChild(self, text):
        return
        file_pos = self._stream.tell()
        self.__updateChild(self.__last_child_stream_pos, self.table_item)
        self.table_item = hmi.hmi.add_table_child(self.table_parent, file_pos, 0, None, text)
        self.__last_child_stream_pos = file_pos 
        if display_filter_actions < self.depth+1: return
        sys.stdout.write("%s[ %s ]\n" % (self.child_indent, text))

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

    def _appendChunk(self, chunk):
        self._chunks.append(chunk)
        id = chunk.id
        if id != None:
            if hasattr(self, id):
                raise Exception("Chunk identifier %s already exist!" % id)
            setattr(self, id, chunk.getData())
            self._chunks_dict[id] = chunk
        print "%sNew chunk: %s, addr=%s, size=%s (file pos=%s)" % (self.indent, chunk.id, chunk.addr, chunk.size, self._stream.tell())

    def readChild(self, id, filter_class, description): 
        self.openChild()
        oldpos = self._stream.tell()
        self.newChild(description)
        filter = filter_class(self._stream, self)
        chunk = FilterChunk(id, filter.description, self._stream, oldpos, self._stream.tell() - oldpos, filter)
        self.closeChild(description)
        print "%s : %s = %s" % (chunk.__class__, chunk.id, chunk.getData())
        self._appendChunk(chunk)
        print "New child chunk"

    def readArray(self, id, filter_class, description, end_func): 
        array = []
        self.openChild()
        addr = self._stream.tell()
        nb = 0
        while not end_func(self._stream):
            oldpos = self._stream.tell()
            self.newChild("New chunk")
            filter = filter_class(self._stream, self)
            chunk_id = "%s[%u]" % (id, nb)
            nb = nb + 1
            chunk = FilterChunk(chunk_id, filter.description, self._stream, oldpos, self._stream.tell() - oldpos, filter)
            array.append( chunk )
        self.closeChild("Chunks")

        chunk = ArrayChunk(id, description, self._stream, addr, self._stream.tell() - addr, array)
        self._appendChunk(chunk)
        print "New chunk array"
    
    def read(self, id, format, description, can_truncate=True):
        format = re.sub(r'\[([^]]+)\]', self.__replaceFieldFormat, format)
#        if self.depth <= display_filter_actions and 0<size:
#            chunk_data.output(self.indent)
#        if can_truncate:
#            data = chunk_data.getData(60)
#        else:
#            data = chunk_data.getData(None)
        chunk = FormatChunk(id, description, self._stream, self._stream.tell(), format)
        self._stream.seek(chunk.size, 1)
        self._appendChunk(chunk)

    def getParent(self): return self._parent

display_filter_actions = 1
