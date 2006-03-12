"""
3D Studio Max file (.3ds) parser.
Author: Victor Stinner
"""

from libhachoir.field import (FieldSet, ParserError,
    Integer, RawBytes, Enum, String, Float)
from libhachoir.parser.image.common import RGB

def readObject(parent):
    yield String(parent, "name", "C", "Object name")
    size = parent["size"].value * 8
    while parent.newFieldAskAddress() < size:
        yield Chunk(parent)

def readTextureFilename(parent):
    yield String(parent, "filename", "C", "Texture filename")

def readVersion(parent):
    yield Integer(parent, "version", "uint32", "3DS file format version")

def readMaterialName(parent):
    yield String(parent, "name", "C", "Material name")

class MapUV(FieldSet):
    endian = "<"
    def __init__(self, parent, name="map[]", description="Mapping UV"):
        FieldSet.__init__(self, parent, name, parent.stream, size=64, description=description)
        
    def createFields(self):
        yield Float(self, "u", "float", "Map U")
        yield Float(self, "v", "float", "Map V")

class Vertex(FieldSet):
    static_size = 12*8
    endian = "<"

    def __init__(self, parent, name="vertex[]", description="Vertex"):
        FieldSet.__init__(self, parent, name, parent.stream, description=description)

    def createFields(self):
        yield Float(self, "x", "float", "X")
        yield Float(self, "y", "float", "Y")
        yield Float(self, "z", "float", "Z")

class Polygon(FieldSet):
    static_size = 64
    endian = "<"
    def createFields(self):
        yield Integer(self, "a", "uint16", "Vertex A")
        yield Integer(self, "b", "uint16", "Vertex B")
        yield Integer(self, "c", "uint16", "Vertex C")
        yield Integer(self, "flags", "uint16", "Flags")

def readMapList(parent):
    yield Integer(parent, "count", "uint16", "Map count")
    for i in range(0, parent["count"].value):
        yield MapUV(parent)

def readColor(parent):
    yield RGB(parent, "color", parent.stream)

def readVertexList(parent):
    yield Integer(parent, "count", "uint16", "Vertex count")
    for i in range(0, parent["count"].value):
        yield Vertex(parent)
    
def readPolygonList(parent):
    count = Integer(parent, "count", "uint16", "Vertex count")
    yield count 
    for i in range(0, count.value):
        yield Polygon(parent, "polygon[]", parent.stream)
    size = parent["size"].value * 8
    while parent.newFieldAskAddress() < size:
        yield Chunk(parent)

class Chunk(FieldSet):
    # List of chunk type name
    type_name = {
        0x0011: "Color",
        0x4D4D: "Main chunk",
        0x0002: "File version",
        0x3D3D: "Materials and objects",
        0x4000: "Object",
        0x4100: "Mesh (triangular)",
        0x4110: "Vertices list",
        0x4120: "Polygon (faces) list",
        0x4140: "Map UV list",
        0x4130: "Object material",
        0xAFFF: "New material",
        0xA000: "Material name",
        0xA010: "Material ambiant",
        0xA020: "Material diffuse",
        0xA030: "Texture specular",
        0xA200: "Texture",
        0xA300: "Texture filename",

        # Key frames
        0xB000: "Keyframes",
        0xB002: "Object node tag",
        0xB006: "Light target node tag",
        0xB007: "Spot light node tag",
        0xB00A: "Keyframes header",
        0xB009: "Keyframe current time",
        0xB030: "Node identifier",
        0xB010: "Node header",
        0x7001: "Viewport layout"
    }

    chunk_id_by_type = {
        0x4d4d: "main",
        0x0002: "version",
        0x3d3d: "obj_mat",
        0xb000: "keyframes",
        0xafff: "material[]",
        0x4000: "object",
        0x4110: "vertices_list",
        0x4120: "polygon_list",
        0x4140: "mapuv_list",
        0x4100: "mesh"
    }

    # List of chunks which contains other chunks
    sub_chunks = \
        (0x4D4D, 0x4100, 0x3D3D, 0xAFFF, 0xA200,
         0xB002, 0xB006, 0xB007,
         0xA010, 0xA030, 0xA020, 0xB000)

    # List of chunk type handlers
    handlers = {
        0xA000: readMaterialName,
        0x4000: readObject,
        0xA300: readTextureFilename,
        0x0011: readColor,
        0x0002: readVersion,
        0x4110: readVertexList,
        0x4120: readPolygonList,
        0x4140: readMapList
    }

    endian = "<"
    
    def __init__(self, parent, name="chunk[]"):
        FieldSet.__init__(self, parent, name, parent.stream)

        # Set description
        self._description = "Chunk: %s" % self["type"].display

        # Set name based on type field
        type = self["type"].value 
        if type in Chunk.chunk_id_by_type:
            self._name = Chunk.chunk_id_by_type[type]
        else:
            self._name = "chunk_%04x" % type

        # Guess chunk size
        self._size = self["size"].value * 8

    def hexadecimal(self, field):
        return "%04X" % field.value    

    def createFields(self):        
        yield Enum(self, "type", "uint16", Chunk.type_name, "Chunk type", text_handler=self.hexadecimal)
        yield Integer(self, "size", "uint32", "Chunk size (in bytes)")
        chunk_size = self["size"].value
        content_size = chunk_size - 6
        type = self["type"].value
        if type in Chunk.sub_chunks:
            while self._total_field_size < chunk_size*8:
                yield Chunk(self)
            assert self._total_field_size == (chunk_size * 8)
        else:
            if type in Chunk.handlers: 
                fields = Chunk.handlers[type] (self)
                for field in fields:
                    yield field
                if self._total_field_size != (chunk_size * 8):
                    raise ParserError( \
                        "Wrong chunk content size (%u bits instead of %u, field %s)"
                        % (self._total_field_size, chunk_size * 8, self.path))
            else:
                yield RawBytes(self, "data", content_size)

class Parser3dsFile(FieldSet):
    mime_types = "image/x-3ds"

    def createFields(self):
        while self._total_field_size < self.stream.size:
            yield Chunk(self)

