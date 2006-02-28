class UniqKeyError(KeyError):
    pass

class IndexedDict:
    def __init__(self):
        self._dict = {}
        self._list = []

    def __getitem__(self, key):
        return self._dict[key]

    def append(self, key, value):
        if key in self._dict:
            raise UniqKeyError("Key '%s' already exists" % key)
        self._dict[key] = value
        self._list.append(value)

    def __len__(self):
        return len(self._list)

    def __contains__(self, key):
        return key in self._dict

    def __iter__(self):
        return iter(self._list)

