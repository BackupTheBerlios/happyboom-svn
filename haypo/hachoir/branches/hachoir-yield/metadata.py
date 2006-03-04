class MetaData:
    pass

class ImageMetaData(MetaData):
    def __init__(self, format, width, height, bits_per_pixel, **kw):
        self.format = format
        self.width = width
        self.height = height
        self.bits_per_pixel = bits_per_pixel

        # Optionnals
        self.nb_colors = kw.get("nb_colors", None)
        self.compression = kw.get("compression", None)

    def __str__(self):
        text = "ImageMetaData <format=%s, size=%sx%s, bpp=%s" % \
            (self.format, self.width, self.height, self.bits_per_pixel)
        if self.nb_colors != None:
            text += ", nb_colors=%s" % self.nb_colors
        if self.compression != None:
            text += ", compression=%s" % self.compression
        return text+">"
    

