"""
3D Studio Max file (.3ds) parser.
Author: Victor Stinner
"""

from filter import Filter
from plugin import registerPlugin

def readTextureFilename(filter, stream):
    filter.readString("filename", "C", "Texture filename")

def readVersion(filter, stream):
    filter.read("version", "<L", "Version")

def readMaterial(filter, stream):
    filter.readString("name", "C", "Material name")
    while not stream.eof():
        filter.readChild("chunk[]", Filter_3DS_Chunk)

def readObject(filter, stream):
    filter.readString("name", "C", "Object name")
    while not stream.eof():
        filter.readChild("chunk[]", Filter_3DS_Chunk)

class Filter_3DS_MapUV(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "3ds_map", "3DS UV map", stream, parent)
        self.read("u", "f", "Map U")
        self.read("v", "f", "Map V")

class Filter_3DS_Vertex(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "3ds_vertex", "3DS vertex", stream, parent)
        self.read("x", "f", "X")
        self.read("y", "f", "Y")
        self.read("z", "f", "Z")

class Filter_3DS_Polygon(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "3ds_polygon", "3DS polygon", stream, parent)
        self.read("a", "<H", "Vertex A")
        self.read("b", "<H", "Vertex B")
        self.read("c", "<H", "Vertex C")
        self.read("flags", "<H", "Flags")
    
def readMapList(filter, stream):
    filter.read("count", "<H", "Map count")
    while not stream.eof():
        filter.readChild("map[]", Filter_3DS_MapUV)

def readColor(filter, stream):
    filter.read("red", "B", "Red componant")
    filter.read("green", "B", "Green componant")
    filter.read("blue", "B", "Blue componant")

def readVertexList(filter, stream):
    filter.read("count", "<H", "Vertex count")
    while not stream.eof():
        filter.readChild("vertex[]", Filter_3DS_Vertex)
    
def readPolygonList(filter, stream):
    filter.read("count", "<H", "Vertex count")
    while not stream.eof():
        filter.readChild("polygon[]", Filter_3DS_Polygon)

class Filter_3DS_Chunk(Filter):
    # List of chunks which contains other chunks
    sub_chunks = \
        (0x4D4D, 0x4100, 0x3D3D, 0xAFFF, 0xA200,
         0xB002, 0xB006, 0xB007,
         0xA010, 0xA030, 0xA020, 0xB000)
    
    def __init__(self, stream, parent):
        Filter.__init__(self, "3ds_chunk", "3DS chunk", stream, parent)
        chunk = self.read("type", "<H", "Chunk type", post=self.toHex)
        chunk.description = "Chunk type (%s)" % self.getType()
        self.read("size", "<L", "Chunk size")
        types = {
            0xA000: readMaterial,
#            0x4000: readObject,
            0xA300: readTextureFilename,
            0x0011: readColor,
            0x0002: readVersion,
# TODO: Uncomment these functions, it's too slow yet            
#            0x4110: readVertexList,
#            0x4120: readPolygonList,
#            0x4140: readMapList
        }
        size = self["size"] - 6
        type = self["type"] 
        end = stream.tell() + size
        if type in Filter_3DS_Chunk.sub_chunks:
            while stream.tell() < end:
                self.readChild("chunk[]", Filter_3DS_Chunk)
            assert stream.tell() == end 
        else:
            if type in types: 
                substream = stream.createSub(size=size)
                types[type] (self, substream)
            else:
                self.read("data", "%us" % size, "Raw data")

    def checkEnd(self, stream, array, last):
        return stream.eof()

    def updateParent(self, chunk):
        type = self.getType()
        chunk.description = "Chunk of type \"%s\"" % type
        self.setDescription("Chunk type (%s)" % type)
        self.setId("chunk_%04x" % self["type"])

    def toHex(self, chunk):
        return "%04X" % chunk.value
        
    def getType(self):
        type = self["type"]
        know = {
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
            0xA000: "New material (name)",
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
        if type in know:
            return know[type]
        else:
            return "%04X" % type 

class Filter_3DS_File(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "3ds_file", "3DS file", stream, parent)
        while not stream.eof():
            self.readChild("chunk[]", Filter_3DS_Chunk)

registerPlugin(Filter_3DS_File, "image/x-3ds")
