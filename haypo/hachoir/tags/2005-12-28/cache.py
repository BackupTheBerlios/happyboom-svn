import gc
from todo import todoWriteMethod

class CacheList:
    _instance = None

    def __init__(self):
        assert CacheList._instance == None
        self._list = []

    def purgeCaches(self):
        size = self.getSize()
        for value in self._list:
            item, name = value
            item.purgeCache()
        gc.collect()            
        print "Purge caches: clear %s item(s)" % size

    def output(self):
        size = 0
        nb_obj = 0
        print "--- Caches"
        for value in self._list:
            item, name = value
            size = item.getCacheSize()
            nb_obj += size
            if size != 0:
                print "o %s: %s item(s)" % (name, size)
        print "--- Total = %s item(s)" % (nb_obj)

    def getSize(self):
        size = 0
        for value in self._list:
            size += value[0].getCacheSize()
        return size           

    def register(self, item, name):
        self._list.append( (item,name) )

    def getInstance():
        if CacheList._instance == None:
            CacheList._instance = CacheList()
        return CacheList._instance
    getInstance = staticmethod(getInstance)

class Cache:
    def __init__(self, name):
        CacheList.getInstance().register(self, name)
    def getCacheSize(self): todoWriteMethod(self, "getCacheSize")
    def purgeCache(self): todoWriteMethod(self, "purgeCache")
