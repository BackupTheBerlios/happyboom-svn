import doctest, sys, os, re
from stat import S_ISREG, ST_MODE

regex_doc_filename = re.compile("^[a-z0-9_-]+\.txt$")

def testDoc(filename, name=None):
    print "--- %s: Run tests" % filename
    doctest.testfile(filename, optionflags=doctest.ELLIPSIS, name=name)
    print "--- %s: End of tests" % filename

def main():
    root_dir = os.path.dirname(__file__)
    hachoir_path = "libhachoir"
    sys.path.append(hachoir_path)

    doc_dir = 'doc'
    documents = os.listdir(doc_dir)
    documents.sort()
    for doc in documents:
        filename = os.path.join(doc_dir, doc)
        if S_ISREG(os.stat(filename)[ST_MODE]) \
        and regex_doc_filename.match(doc) != None:
            testDoc(filename)

if __name__ == "__main__":
    main()
