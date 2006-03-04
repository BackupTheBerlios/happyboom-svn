#!/usr/bin/env python

from file.image.png import PngFile, PngMetaData
from file.image.bmp import BmpFile, BmpMetaData
from file.image.pcx import PcxFile, PcxMetaData
from stream.file import FileStream
from text_ui import displayFieldSet
import sys

def main():
    if 2 <= len(sys.argv):
        filename = sys.argv[1]
    else:
        filename = "/home/haypo/exemple/png.png"
    stream = FileStream(open(filename, 'r'), filename)
    if filename.endswith(".png"):
        png = PngFile(None, "png_file", stream)
        print "[Picture %s]" % filename
        meta = PngMetaData(png) ; print meta
#        displayFieldSet(png)
    elif filename.endswith(".pcx"):
        pcx = PcxFile(None, "pcx_file", stream)
        displayFieldSet(pcx, 2)
        meta = PcxMetaData(pcx) ; print meta
    else:
        bmp = BmpFile(None, "bmp_file", stream)
        displayFieldSet(bmp)
        meta = BmpMetaData(bmp) ; print meta

if __name__ == "__main__":
    main()
