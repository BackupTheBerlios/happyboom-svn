import thread
import time

class NetBuffer:
    """ Buffer used to store network packets. Support multithreading.
    @ivar blocking_read_sleep : Sleep duration when waiting data from network.
    @type blocking_read_sleep: C{float}
    @ivar __buffer: Buffer which store network packets.
    @type __buffer: C{list<L{Packet<io.Packet>}>}
    """
    
    def __init__(self):
        """ Constructor. """
        self.blocking_read_sleep = 0.010
        self.__buffer = {} 
        self.__sema = thread.allocate_lock()

    def clear(self, key):
        """ Clear buffer. """
        self.__sema.acquire()
        self.__buffer[key] = [] 
        self.__sema.release()
    
    def append(self, key, data):
        """ Append new data to the buffer. """
        self.__sema.acquire()
        if self.__buffer.has_key(key):
            self.__buffer[key].append(data)
        else:
            self.__buffer[key] = [data]
        self.__sema.release()

    def readNonBlocking(self, key):
        """ Read one data. Returns None if their is no data.
        @rtype: C{str}
        """
        self.__sema.acquire()
        buffer = self.__buffer.get(key, [])
        self.__buffer[key] = []
        self.__sema.release()
        return buffer

    def readBlocking(self, key, timeout):
        """ Read one data.
        Returns None if their is no data after the timeout.
        @type timeout: C{float}
        @rtype: C{str}
        """
        data = None
        timeout = time.time()+timeout
        while data == None:
            if timeout < time.time(): break
            self.__sema.acquire()
            if self.__buffer.has_key(key) and len(self.__buffer[key]) != 0:
                data = self.__buffer[key][0]
                del self.__buffer[key][0] 
            self.__sema.release()
            if data == None: time.sleep(self.blocking_read_sleep)
        return data
