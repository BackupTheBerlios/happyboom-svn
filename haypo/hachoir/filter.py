"""
Base class for all splitter filters.
"""

import struct
import re
import sys
import types
import string

class Filter:
    def __init__(self, stream, parent=None):
        self._sub_struct = {}
        self.stream = stream
        self.parent = parent
        if self.parent:
            self.depth = parent.depth + 1
        else:
            self.depth = 1
        self.indent = " " * ((self.depth-1)*2)
        self.child_indent = " " * (self.depth*2)

    def __replaceFieldFormat(self, match):
        return str(getattr(self, match.group(1)))

    def openChild(self):
        self.__child_stream_pos = self.stream.tell()

    def closeChild(self, text):
        if display_filter_actions != self.depth: return
        size = self.stream.tell() - self.__child_stream_pos
        sys.stdout.write("%s<%s (%u bytes)>\n" % (self.indent, text, size))

    def newChild(self, text):
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
        max = 80 
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
            # Write indentation
            sys.stdout.write(self.indent)

            # Write first 4 bytes in hexadecimal
            i = 0
            for byte in rawdata:
                # If there are more than 4 bytes, write "..."
                if 4 <= i:
                    sys.stdout.write(".. ")
                    i = i + 1
                    break
                sys.stdout.write("%02X " % ord(byte))
                i = i + 1

            # Align text to 4 bytes
            sys.stdout.write("   " * (5-i))

            # Write description
            sys.stdout.write("%s (%u bytes)" % (description, size))

            # Write content like id=value?
            if id != None:
                t = type(data)
                if t==types.IntType or t==types.LongType:
                    # Display integers
                    sys.stdout.write(", %s = %u" % (id, data))
                elif type(data)==types.StringType and len(data)<max:
                    # Display string (replace ASCII < 32 by \xCC)
                    display = re.sub("([\x00-\x1F])", lambda m: "\\x%02X" % ord(m.group(1)), data)
                    if self.__isStrPrintable(display):
                        sys.stdout.write(", %s=\"%s\"" % (id, display))
            sys.stdout.write("\n")

        # Save result in the object
        if id != None:
            setattr(self, id, data)

display_filter_actions = 1
