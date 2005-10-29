"""
Base class for all splitter filters.
"""

import struct
import re
import sys
import types
import string
import hmi

class Filter:
    def __init__(self, stream, parent=None):
        self._sub_struct = {}
        self.stream = stream
        self.parent = parent
        if self.parent:
            self.depth = parent.depth + 1
            self.table_parent = parent.table_item
        else:
            self.depth = 1
            self.table_item = None
            self.table_parent = None 
        self.indent = " " * ((self.depth-1)*2)
        self.child_indent = " " * (self.depth*2)
        self.table_item = None
        self.__last_child_stream_pos = None 

    def __replaceFieldFormat(self, match):
        return str(getattr(self, match.group(1)))

    def openChild(self):
        self.__child_stream_pos = self.stream.tell()
        self.__last_child_stream_pos = None 

    def closeChild(self, text):
        self.__updateChild(self.__last_child_stream_pos, self.table_item)
        if self.table_parent != None:
            self.__updateChild(self.__child_stream_pos, self.table_parent)
        self.table_item = None
        self.__last_child_stream_pos = None
        if display_filter_actions != self.depth: return
        size = self.stream.tell() - self.__child_stream_pos
        sys.stdout.write("%s<%s (%u bytes)>\n" % (self.indent, text, size))

    def __updateChild(self, pos, table):
        if pos == None or table == None: return False
        size = self.stream.tell() - pos
        hmi.hmi.set_table_value(table, 1, size) 
        return True

    def updateChildTitle(self, text):
        hmi.hmi.set_table_value(self.table_item, 4, text) 

    def newChild(self, text):
        file_pos = self.stream.tell()
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
        lg = self.stream.searchLength(delimiter, False)
        if lg == -1:
            raise Exception("Delimiter \"%s\" not found for %s (%s)!" % (delimiter, id, description))
        self.read(id, "!%us" % lg, description) 
        self.read(None, "!%us" % len(delimiter), "Delimiter of %s" % id) 

    def searchEol(self, eol):
        lg = self.stream.searchLength(eol, True)
        if lg == -1:
            return self.stream.getLastPos() - self.stream.tell()
        else:
            return lg

    def readLine(self, id, description, eol="\n", fails_if_not_found=False, can_truncate=False):
        lg = self.searchEol(eol)
        self.read(id, "!%us" % lg, description, can_truncate)
        line = getattr(self, id)
        setattr(self, id, line[:-len(eol)])
        
    def read(self, id, format, description, can_truncate=True):
        format = re.sub(r'\[([^]]+)\]', self.__replaceFieldFormat, format)
        size = struct.calcsize(format)
        max = 60 
        if size<max or format[-1] != "s" or not can_truncate:
            rawdata = self.stream.getN(size)
            assert len(rawdata) == size
            data = struct.unpack(format, rawdata)
            data = data[0]
        else:
            rawdata = self.stream.getN(max)
            assert len(rawdata) == max
            data = rawdata + "(...)"
            self.stream.seek( self.stream.tell() + size - max )
        # Display content ?
        if self.depth <= display_filter_actions and 0<size:
            file_pos = self.stream.tell() - size

            # Convert data into hexadecimal
            i = 0
            hex_data = ""
            for byte in rawdata:
                # If there are more than 4 bytes, write "..."
                if 4 <= i:
                    hex_data = hex_data + ".. "
                    i = i + 1
                    break
                hex_data = hex_data + "%02X " % ord(byte)
                i = i + 1

            # Write "<addr>: <indent><hex data>"
            sys.stdout.write("%08X: %s%s" % (file_pos, self.indent, hex_data))

            # Align text to 4 bytes
            sys.stdout.write("   " * (5-i))

            # Write description
            sys.stdout.write("%s (%u bytes)" % (description, size))

            # Write content like id=value?
            comment = ""
            if id != None:
                t = type(data)
                if t==types.IntType or t==types.LongType:
                    # Display integers
                    comment = "%s = %u" % (id, data)
                elif type(data)==types.StringType and len(data)<max:
                    # Display string (replace ASCII < 32 by \xCC)
                    display = ""
                    for c in data:
                        if ord(c)<32:
                            know = {"\n": "\\n", "\r": "\\r"}
                            if c in know:
                                display = display + know[c]
                            else:
                                display = display + "\\x%02X" % ord(c)
                        elif c in string.printable:
                            display = display + c
                        else:
                            display = display + "."
                    comment = "%s=\"%s\"" % (id, display)
            if comment != "":
                sys.stdout.write(comment)
            sys.stdout.write("\n")
            hmi.hmi.add_table(self.table_parent, file_pos, size, hex_data, id, description, comment)

        # Save result in the object
        if id != None:
            setattr(self, id, data)

display_filter_actions = 1
