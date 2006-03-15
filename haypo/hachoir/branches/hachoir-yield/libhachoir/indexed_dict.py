class UniqKeyError(KeyError):
    pass

class OrderedDict:
    """
    This class works like classic Python dict() but has an important method:
    __iter__() which allow to iterate into the dictionnary _values_ (and not
    keys like Python's dict does).
    """
    def __init__(self):
        self._dict = {}         # key => value
        self._value_list = []   # index => value

    def getByIndex(self, index):
        return self._value_list[index]

    def __getitem__(self, key):
        return self._dict[key]

    def append(self, key, value):
        if key in self._dict:
            raise UniqKeyError("Key '%s' already exists" % key)
        self._dict[key] = value
        self._value_list.append(value)

    def __len__(self):
        return len(self._value_list)

    def __contains__(self, key):
        return key in self._dict

    def __iter__(self):
        return iter(self._value_list)

class IndexedDict(OrderedDict):
    """
    This class is based on OrderedDict(), but add new methods:
      * indexOf(key)
      * insert(index, key, value) 
      * __delitem__(index)
    """
    
    def __init__(self):
        self._key_list = []     # index => key, needed by insert
        self._index = {}        # key => index

    def indexOf(self, key):
        return self._index[key]

    def append(self, key, value):
        OrderedDict.append(key, value)
        self._index[key] = len(self._value_list)-1
        self._key_list.append(key)
        
    def __delitem__(self, index):
        key = self._key_list[index]
        for index_key in self._key_list[index+1:]:
            self._index[index_key] -= 1
        del self._dict[key]
        del self._value_list[index]
        del self._key_list[index]

    def insert(self, index, key, value):
        if key in self:
            raise UniqKeyError("Insert error: key '%s' ready exists" % key)
        if index < 0:
            if not(-len(self._key_list) <= index):
                raise IndexError("Insert error: index '%s' is invalid" % index)
            index = len(self._key_list)+index
        else:                
            if not(0 <= index <= len(self._key_list)):
                raise IndexError("Insert error: index '%s' is invalid" % index)
        for index_key in self._key_list[index:]:
            self._index[index_key] += 1         
        self._dict[key] = value
        self._index[key] = index 
        self._value_list.insert(index, value)
        self._key_list.insert(index, key)

