#!/usr/bin/env python

from file.image.png import PngFile, PngMetaData
from stream.file import FileStream
from text_ui import displayFieldSet
import sys

def main():
    if 2 <= len(sys.argv):
        filename = sys.argv[1]
    else:
        filename = "/home/haypo/exemple/png.png"
    stream = FileStream(open(filename, 'r'), filename)
    png = PngFile(None, "png_file", stream)
    print "[Picture %s]" % filename
    meta = PngMetaData(png) ; print meta
#    displayFieldSet(png)

if __name__ == "__main__":
    main()
