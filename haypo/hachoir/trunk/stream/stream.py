import struct
from error import StreamError
from tools import regexMaxLength
from format import getRealFormat, getFormatSize

class Stream:
    def __init__(self, filename):
        self.filename = filename
    
    #--- Virtual functions --------------------------------------------------
    
    def getSize(self):
        return 0

    def clone(self):
        return None
    
    def getLastPos(self):
        return 0

    def tell(self):
        return 0
    
    def read(self, size, seek=True):
        """ Works like Posix read (can returns less than size bytes. """
        return None
    
    def getN(self, size, seek=True):
        """
        Read size bytes. If seek=False, stay at the same position in the
        stream. This function always returns size bytes, else it raise an
        exception (StreamError).
        """
        return None
    
    #--- End of virtual functions -------------------------------------------    

    def getType(self):
        return self.__class__.__name__

    def eof(self):
        return self.getLastPos() <= self.tell() 

    def createSub(self, start=None, size=None):
        if start==None:
            start = self.tell()
        if size == None:
            size = self.getSize()-start
        return SubStream(self, start, size, self.filename)

    def createLimited(self, start=None, size=None):
        if start==None:
            start = self.tell()
        if size == None:
            size = self.getSize()-start
        return LimitedStream(self, start, size, self.filename)

    def getFormat(self, format, seek=True):
        """
        Read data using struct format. Eg. getFormat("BB") returns (10, 14).
        """
        size = getFormatSize(format)
        real = getRealFormat(format)
        data = self.getN(size, seek)
        return struct.unpack(real, data)[0]

    def searchLength(self, needle, include_str, size_max=None):        
        pos = self.search(needle, size_max)
        if pos == -1: return -1
        lg = pos - self.tell()
        if include_str:
            if isinstance(needle, str):
                lg = lg + len(needle)
            else:
                lg = lg + regexMaxLength(needle.pattern)
        return lg
  
    def search(self, needle, size_max=None):
        size = self.getSize()
        if size == 0: return -1
        if size_max != None:
            pos_max = self.tell()+size_max
            if size <= pos_max:
                pos_max = size-1
        else:
            pos_max = size-1
        assert 0<=pos_max  and pos_max<size
        oldpos = self.tell()
        pos = self._doSearch(needle, pos_max)
        self.seek(oldpos)
        return pos

    def _doSearch(self, needle, pos_max):
        """
        Search a string between current position and pos_max (which will be
        also tested). Returns -1 if fails.
        """
        is_regex =  not isinstance(needle, str)
        if is_regex:
            len_needle = regexMaxLength(needle.pattern)
        else:
            len_needle = len(needle)
        if 2048<=len_needle:
            raise StreamError("Search string too big.")
        size = 2048 
        doublesize = size * 2
        oldpos = self.tell()
        max = pos_max-oldpos+1
        if max<doublesize:
            doublesize = max 
            size = 0 
        buffer = self.read(doublesize)
        newpos = oldpos + size
        while len(buffer) != 0:
            if is_regex:
                match = needle.search(buffer)
                if match != None:
                    pos = match.start(0)
                else:
                    pos = -1
            else:
                pos = buffer.find(needle)
            if pos != -1: return oldpos + pos
            oldpos = newpos
            if pos_max < oldpos + size:
                size = pos_max - oldpos
            if size == 0:
                break
            buffer = buffer[size:] + self.read(size)
            newpos = oldpos + size 
        return -1 

class LimitedStream(Stream):
    def __init__(self, stream, start=0, size=0, filename=None):
        Stream.__init__(self, filename)
        assert 1 <= size            
        assert 0 <= start
        assert not(stream.getLastPos()+1 < start+size)
        self._stream = stream.clone()
#        if start<0:
#            start = 0
#        if self._stream.getLastPos()+1 < start+size:
#            size = self._stream.getLastPos()-start+1
        self._start = start
        self._size = size
        self._end = self._start + self._size
        self._last_pos = self._end - 1
        self._stream.seek(self._start)

    def getType(self):
        return "%s of %s: %s..%s" % \
            (self.__class__.__name__, self._stream.getType(),
             self._start, self._end)
 
    def search(self, str, size_max=None):
        if self._end == 0: return -1
        if size_max == None or self._end-self.tell() < size_max:
            size_max = self._end-self.tell()
        assert 0<=size_max  and size_max<=self._size
        return self._stream.search(str, size_max)
        
    def read(self, size, seek=True):
        """ Works like Posix read (can returns less than size bytes. """
        return self._stream.read(size, seek)

    def getN(self, size, seek=True):
        if self._start+self._size<self._stream.tell()+size:
            raise StreamError( \
                "Can't read outsize the stream\n"
                +"(try to read %u byte(s) from position %s, where stream in limited in [%u;%u])" \
                % (size, self._stream.tell(), self._start, self._end))
        return self._stream.getN(size, seek)

    def tell(self):
        return self._stream.tell()

    def seek(self, pos, where=0):
        if where == 2:
            pos = self.getLastPos() - pos
        elif where == 0:
            pos = pos
        elif where == 1:
            pos = self._stream.tell() + pos
        assert self._start <= pos and pos <= self._end
        self._stream.seek(pos, 0)
        
    def getSize(self):
        return self._size
    
    def getLastPos(self):
        return self._last_pos

    def clone(self):
        return LimitedStream(self._stream, self._start, self._size, self.filename)

class SubStream(LimitedStream):
    def search(self, str, size_max=None):
        if self._end == 0: return -1
        max = self._end-self.tell()-self._start-1
        if size_max == None or max < size_max:
            size_max = max
        assert 0<=size_max  and size_max<=self._size
        pos = self._stream.search(str, size_max)
        if pos != -1:
            pos = pos - self._start
        return pos
               
    def read(self, size, seek=True):
        """ Works like Posix read (can returns less than size bytes. """
        return self._stream.read(size, seek)
 
    def seek(self, pos, where=0):
        if where == 2:
            pos = self.getLastPos() - pos
        elif where == 0:
            pos = self._start + pos
        elif where == 1:
            pos = self._stream.tell() + pos
        assert self._start <= pos and pos <= self._end
        self._stream.seek(pos, 0)

    def tell(self):
        return self._stream.tell() - self._start
    
    def getLastPos(self):
        return self._end - self._start

    def clone(self):
        return SubStream(self._stream, self._start, self._size, self.filename)
