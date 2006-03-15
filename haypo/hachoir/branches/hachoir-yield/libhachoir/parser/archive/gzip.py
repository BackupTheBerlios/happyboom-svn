"""
GZIP archive parser.

Author: Victor Stinner
"""

from field import (FieldSet, 
    Integer, Enum, 
    Bit, Bits,
    RawBytes,  String)
from error import error
from text_handler import hexadecimal, humanFilesize, unixTimestamp
import datetime

def removeField(field_set, delete_field):
    size = delete_field.size
    index = field_set.fields.indexOf(delete_field.name)
    fields = field_set.fields
    for update_index in xrange(index+1, len(fields)):
        field = fields.getByIndex(update_index)
        field.address -= size
    del field_set.fields[index]
    
def insertFieldAfter(field_set, after, new_field):
    print new_field.path
    size = new_field.size
    index = field_set.fields.indexOf(after.name)
    fields = field_set.fields
    for update_index in xrange(index+1, len(fields)):
        field = fields.getByIndex(update_index)
        field.address += size
    print "Insert %s after %s" % (new_field.path, after.path)
    new_field.address = after.address + after.size
    field_set.fields.insert(index+1, new_field.name, new_field)
   
class GzipFile(FieldSet):
    mime_types = "application/x-gzip"
    os_name = {
        0: "FAT filesystem",
        1: "Amiga",
        2: "VMS (or OpenVMS)",
        3: "Unix",
        4: "VM/CMS",
        5: "Atari TOS",
        6: "HPFS filesystem (OS/2, NT)",
        7: "Macintosh",
        8: "Z-System",
        9: "CP/M",
        10: "TOPS-20",
        11: "NTFS filesystem (NT)",
        12: "QDOS",
        13: "Acorn RISCOS"} 
    endian = "<"

    def fieldValueChanged(self, field):
        if field.name == "has_comment":
            if field.value:
                assert "comment" not in self
                if self["has_filename"].value:
                    after = self["filename"]
                elif self["has_extra"].value:
                    after = self["extra"]
                else:
                    after = self["os"]
                value = "abc"
                comment = String(self, "comment", "string[%u]" % len(value), description="Comment", value=value)
                insertFieldAfter(self, after, comment)
            else:
                removeField(self, self["comment"])

    def createFields(self):
        # Install handlers
        self.connectEvent("field-value-changed", self.fieldValueChanged)
    
        # Gzip header
        yield RawBytes(self, "id", 2, "GZip identifier")
        assert self["id"].value == "\x1f\x8b" 
        yield Integer(self, "compression", "uint8", "Compression method", text_handler=self.getCompressionMethod)
        
        # Flags
        yield Bit(self, "is_text", "File content is probably ASCII text")
        yield Bit(self, "has_crc16", "Header CRC16")
        yield Bit(self, "has_extra", "Extra informations (variable size)")
        yield Bit(self, "has_filename", "Contains filename?")
        yield Bit(self, "has_comment", "Contains comment?")
        yield Bits(self, "unused1", 3, "(unused bits)")
        yield Integer(self, "mtime", "uint32", "Modification time", text_handler=unixTimestamp)

        # Extra flags
        yield Bit(self, "unused2", "(unused bit)")
        yield Bit(self, "slowest", "Compressor used maximum compression (slowest)")
        yield Bit(self, "fastest", "Compressor used the fastest compression")
        yield Bits(self, "unused3", 5, "(unused bits)")

        yield Enum(self, "os", "uint8", GzipFile.os_name, "Operating system")

        # Optionnal fields
        if self["has_extra"].value:
            yield Integer(self, "extra_length", "uint16", "Extra length")
            yield RawBytes(self, "extra", self["extra_length"].value, "Extra")
        if self["has_filename"].value:
            yield String(self, "filename", "C", "Filename")
        if self["has_comment"].value:
            yield String(self, "comment", "C", "Comment")
        if self["has_crc16"].value:
            yield Integer(self, "hdr_crc16", "uint16", "CRC16 of the header", text_handler=hexadecimal)

        # Read content           
        size = self.stream.size - self.newFieldAskAddress() - 8*8
        assert (size % 8) == 0
        yield RawBytes(self, "data", size/8, "Compressed data")

        # Footer
        yield Integer(self, "crc32", "uint32", "Uncompressed data content CRC32", text_handler=hexadecimal)
        yield Integer(self, "size", "uint32", "Uncompressed size", text_handler=humanFilesize)

    def getCompressionMethod(self, chunk):
        if chunk.value < 8:
            return "reserved"
        elif chunk.value == 8:
            return "deflate"
        else:
            return "Unknow (%s)" % val

