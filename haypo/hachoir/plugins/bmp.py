"""
Microsoft Bitmap picture parseer.

Author: Victor Stinner
Creation: 16 december 2005
"""

from filter import Filter
from plugin import registerPlugin

class BitmapFile(Filter):
    def __init__(self, stream, parent):
        Filter.__init__(self, "bmp_file", "Bitmap picture file (BMP)", stream, parent)
        self.read("header", "!2s", "Header (\"BM\")")
        self.read("file_size", "<L", "File size (bytes)")
        self.read("notused", "<L", "Reseved")
        self.read("data_start", "<L", "Data start position")
        header_size = self.read("header_size", "<L", "Header size").value
        assert header_size in (12, 40)
        self.read("width", "<L", "Width (pixels)")
        self.read("height", "<L", "Height (pixels)")
        self.read("nb_plan", "<H", "Number of plan (=1)")
        self.read("bits_pixel", "<H", "Bits per pixel")
        if header_size == 40:
            self.read("compression", "<L", "Compression method")
            self.read("image_size", "<L", "Image size (bytes)")
            self.read("horizontal_dpi", "<L", "Horizontal DPI")
            self.read("vertical_dpi", "<L", "Vertical DPI")
            self.read("used_colors", "<L", "Number of color used")
            self.read("important_color", "<L", "Number of import colors")

registerPlugin(BitmapFile, "image/x-ms-bmp")
