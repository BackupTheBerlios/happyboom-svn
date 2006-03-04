import doctest, sys, os

def testDoc(filename, name=None):
    print "Run test in %s" % filename
    doctest.testfile(filename, optionflags=doctest.ELLIPSIS, name=name)
    print "End of all tests of %s" % filename

def main():
    root_dir = os.path.dirname(__file__)
    hachoir_path = "libhachoir"
    sys.path.append(hachoir_path)

    testDoc('doc/doc.txt', "Main document")

if __name__ == "__main__":
    main()
