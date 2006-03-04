from file.image.png import PngFile
from file.image.pcx import PcxFile
from file.image.bmp import BmpFile

class MetaData:
    def __str__(self):
        raise NotImplementedError()

class ImageMetaData(MetaData):
    def __init__(self, width, height, bits_per_pixel, **kw):
        self.width = width
        self.height = height
        self.bits_per_pixel = bits_per_pixel

        # Optionnals
        self.nb_colors = kw.get("nb_colors", None)
        self.compression = kw.get("compression", None)
        self.format = kw.get("format", None)

    def __str__(self):
        text = "Image: "
        if self.format != None:
            text += "format=%s, " % self.format 
        text += "size=%sx%s, bpp=%s" % \
            (self.width, self.height, self.bits_per_pixel)
        if self.nb_colors != None:
            text += ", nb_colors=%s" % self.nb_colors
        if self.compression != None:
            text += ", compression=%s" % self.compression
        return text

class BmpMetaData(ImageMetaData):
    def __init__(self, bmp):
        width, height = bmp["width"].value, bmp["height"].value
        bpp = bmp["bpp"].value
        if "used_colors" in bmp:
            nb_colors = bmp["used_colors"].value 
        else:
            nb_colors = None
        if bmp["compression"].value != 0:
            compression = "(compressed)"
        else:
            compression = "No"
        ImageMetaData.__init__(self, width, height, bpp, nb_colors=nb_colors)

class PcxMetaData(ImageMetaData):
    def __init__(self, pcx):
        width, height = pcx["xmax"].value+1, pcx["ymax"].value+1
        bpp = pcx["bpp"].value
        ImageMetaData.__init__(self, width, height, bpp)

class PngMetaData(ImageMetaData):
    def __init__(self, png):
        header = png["/header/content"]
        color_type = header["color_type"]
        width, height = header["width"].value, header["height"].value
        bpp = header["bpp"].value
        if color_type["palette"].value:
            nb_colors = png["/palette/content"].nb_colors
        else:
            nb_colors = None
        if color_type["alpha"].value:
            format = "RGBA"
        else:
            format = "RGB"
#        if header["compression"].value != 0:
#            compression = "(compressed)"
#        else:
#            compression = "No"
        ImageMetaData.__init__(self, width, height, bpp, \
            nb_colors=nb_colors, format=format)

_metadata_class = {
    PngFile: PngMetaData,
    PcxFile: PcxMetaData,
    BmpFile: BmpMetaData
}    

def createMetaData(field_set):
    """
    Create a MetaData class from a FieldSet instance.
    Returns None if we don't know about this format
    """
    cls = field_set.__class__
    if cls not in _metadata_class:
        return None
    return _metadata_class[cls] (field_set)

