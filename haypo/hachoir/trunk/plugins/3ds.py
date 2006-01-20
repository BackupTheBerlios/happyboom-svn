"""
3D Studio Max file (.3ds) parser.
Author: Victor Stinner
"""

from filter import OnDemandFilter, OnDemandFilter
from chunk import FormatChunk, StringChunk
from plugin import registerPlugin

def readTextureFilename(filter, stream, last_pos):
    filter.read("filename", "Texture filename", (StringChunk, "C"))

def readVersion(filter, stream, last_pos):
    filter.read("version", "Version", (FormatChunk, "uint32"))

def readMaterialName(filter, stream, last_pos):
    filter.read("name", "Material name", (StringChunk, "C"))

def readObject(filter, stream, last_pos):
    chunk = filter.read("name", "Object name", (StringChunk, "C"))
    while stream.tell() < last_pos:
        filter.read("chunk[]", "Chunk", (Filter_3DS_Chunk,))

class Filter_3DS_MapUV(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "3ds_map", "3DS UV map", stream, parent, "<")
        self.read("u", "Map U", (FormatChunk, "float"))
        self.read("v", "Map V", (FormatChunk, "float"))

    @staticmethod
    def getStaticSize(stream, args):
        return 4*2
 
class Filter_3DS_Vertex(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "3ds_vertex", "3DS vertex", stream, parent, "<")
        self.read("x", "X", (FormatChunk, "float"))
        self.read("y", "Y", (FormatChunk, "float"))
        self.read("z", "Z", (FormatChunk, "float"))

    @staticmethod
    def getStaticSize(stream, args):
        return 4*3

class Filter_3DS_Polygon(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "3ds_polygon", "3DS polygon", stream, parent, "<")
        self.read("a", "Vertex A", (FormatChunk, "uint16"))
        self.read("b", "Vertex B", (FormatChunk, "uint16"))
        self.read("c", "Vertex C", (FormatChunk, "uint16"))
        self.read("flags", "Flags", (FormatChunk, "uint16"))

    @staticmethod
    def getStaticSize(stream, args):
        return 4*2
    
def readMapList(filter, stream, last_pos):
    filter.read("count", "Map count", (FormatChunk, "uint16"))
    for i in range(0, filter["count"]):
        filter.read("map[]", "Map UV", (Filter_3DS_MapUV,))

def readColor(filter, stream, last_pos):
    filter.read("red", "Red componant", (FormatChunk, "uint8"))
    filter.read("green", "Green componant", (FormatChunk, "uint8"))
    filter.read("blue", "Blue componant", (FormatChunk, "uint8"))

def readVertexList(filter, stream, last_pos):
    filter.read("count", "Vertex count", (FormatChunk, "uint16"))
    for i in range(0, filter["count"]):
        filter.read("vertex[]", "Vertex", (Filter_3DS_Vertex,))
    
def readPolygonList(filter, stream, last_pos):
    filter.read("count", "Vertex count", (FormatChunk, "uint16"))
    for i in range(0, filter["count"]):
        filter.read("polygon[]", "Polygon", (Filter_3DS_Polygon,))
    while stream.tell() < last_pos:
        filter.read("chunk[]", "Chunk", (Filter_3DS_Chunk,))

class Filter_3DS_Chunk(OnDemandFilter):
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
        0xafff: "material",
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
    
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "3ds_chunk", "3DS chunk", stream, parent, "<")
        chunk = self.doRead("type", "Chunk type", (FormatChunk, "uint16"), {"post": self.toHex})
        chunk.description = "Chunk type (%s)" % self.getType()
        self.read("size", "Chunk size", (FormatChunk, "uint32"))
        size = self["size"] - 6
        type = self["type"] 
        end = stream.tell() + size
        if type in Filter_3DS_Chunk.sub_chunks:
            while stream.tell() < end:
                self.read("chunk[]", "Chunk", (Filter_3DS_Chunk,))
            assert stream.tell() == end 
        else:
            if type in Filter_3DS_Chunk.handlers: 
                end = stream.tell() + size
                Filter_3DS_Chunk.handlers[type] (self, stream, end)
                assert stream.tell() == end
            else:
                self.read("data", "Raw data", (FormatChunk, "string[%u]" % size))

    def checkEnd(self, stream, array, last):
        return stream.eof()

    def updateParent(self, chunk):
        type = self.getType()
        chunk.description = "Chunk: %s" % type
        if self["type"] in Filter_3DS_Chunk.chunk_id_by_type:
            id = Filter_3DS_Chunk.chunk_id_by_type[self["type"]]
            chunk.id = id
        else:
            chunk.id = "chunk_%04x" % self["type"]

    def toHex(self, chunk):
        return "%04X" % chunk.value
        
    def getType(self):
        type = self["type"]
        return Filter_3DS_Chunk.type_name.get(type, "%04X" % type)

class Filter_3DS_File(OnDemandFilter):
    def __init__(self, stream, parent):
        OnDemandFilter.__init__(self, "3ds_file", "3DS file", stream, parent)
        while not stream.eof():
            self.read("chunk[]", "Chunk", (Filter_3DS_Chunk,))

registerPlugin(Filter_3DS_File, "image/x-3ds")
