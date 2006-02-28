#!/usr/bin/env python

from file.image.png import PngFile
from stream.file import FileStream
from text_ui import displayFieldSet

def valueChanged(field):
    print "Value of %s changed to %s" % (field._name, field.value)

def main():
    filename = "/home/haypo/exemple/png.png"
    stream = FileStream(open(filename, 'r'), filename)
    png = PngFile(None, "png_file", stream)
    displayFieldSet(png)

if __name__ == "__main__":
    main()
