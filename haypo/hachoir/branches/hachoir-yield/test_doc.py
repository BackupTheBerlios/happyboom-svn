import doctest
filename = 'doc.txt'
print "Run test in %s" % filename
doctest.testfile(filename, optionflags=doctest.ELLIPSIS)
print "End of all tests of %s" % filename

