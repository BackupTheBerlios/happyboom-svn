#!/usr/bin/env python
import sys, os, getopt
from text_ui import displayFieldSet

def main():
    current_dir = os.path.dirname(__file__)
    libhachoir_path = os.path.join(current_dir, "libhachoir")
    sys.path.append(libhachoir_path)

    from libhachoir.parser.archive.gzip import GzipFile
    from libhachoir.stream import FileInputStream, FileOutputStream

    input = FileInputStream("/home/haypo/exemple/gz.gz")
    gzip = GzipFile(None, "gzip", input)

#    displayFieldSet(gzip)
    
    print "Set has_comment=True"
    gzip["has_comment"].value = True 
    print "Set has_comment=True: done"

    output = FileOutputStream("/home/haypo/new.gz")
#    gzip.writeInto(output)
    displayFieldSet(gzip)
    
main()
