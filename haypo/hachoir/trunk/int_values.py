# 10
# (10,12)
# [1,2,3]
# [1, (3,4), 6]        
class IntValues:
    def __init__(self, data=None):
        self.items = None
        self.min = None
        self.max = None
        if data != None:
            self.set(data)

    def __hash__(self):
        return hash(self.items)

    def hasValue(self, value):
        return self._in(self.items, value)
        
    def _in(self, values, x):
        if isinstance(values, tuple):
            return values[0] <= x and x <= values[1]
        elif isinstance(values, list):
            result = 0
            for item in values:
                if self._in(item, x):
                    return True
            return False
        elif values != None:        
            return values == x
        else:
            return False

    def set(self, value):
        self.items = None
        self.min = self.max = None
        self.add(value)

    def __str__(self):
        return str(self.items)        

    def isEmpty(self):
        return self.items == None

    def __len__(self):
        return self._length(self.items)
        
    def _length(self, values):
        if isinstance(values, tuple):
            return values[1] - values[0] + 1
        elif isinstance(values, list):
            result = 0
            for item in values:
                result += self._length(item)
            return result
        elif values != None:        
            return 1 
        else:
            return 0

    def values(self):
        return self._values(self.items)

    def __iter__(self):
        for x in self.values():
            yield x

    def _values(self, values):
        if isinstance(values, tuple):
            return range(values[0], values[1]+1)
        elif isinstance(values, list):
            result = []
            for item in values:
                result.extend( self._values(item) )
            return result
        elif values != None:        
            return [values]
        else:
            return []

    def add(self, new):
        if isinstance(new, IntValues):
            new = new.items

        # TODO: Fix that!
        if isinstance(new, int):
            if self.min == None or new < self.min:
                self.min = new
            if self.max == None or new > self.max:
                self.max = new
        elif isinstance(new, tuple):
            if self.min == None or new[0] < self.min:
                self.min = new[0]
            if self.max == None or new[1] > self.max:
                self.max = new[1]

        if isinstance(self.items, tuple):
            if isinstance(new, tuple):
                if self.items[0] <= new[0] and new[1] <= self.items[1]:
                    return
                assert False # TODO: Finish ..
            elif isinstance(new, int):
                if (new - self.items[1]) == 1:
                    self.items = (self.items[0], new)
                else:
                    self.items = [self.items, new]
            else:            
                assert False # TODO: Finish ..
            return
        elif isinstance(self.items, list):
            for index in range(0, len(self.items)):
                item = self.items[index]
                if item == new:
                    return
                print "two"
                if isinstance(item, int) and new < item:
                    self.items.insert(index-1, new)
                    return
                if isinstance(item, tuple) and (new-item[1])==1:
                    self.items[index] = (item[0], new)
                    return
                if isinstance(new, tuple) and new[1] < item:
                    self.items.insert(index-1, new)
                    return

            # Can create an interval?
            item = self.items[-1]
            if isinstance(item, int) and isinstance(new, int) and (new-item) == 1:
                self.items[-1] = (item, new)
                return

            if isinstance(new, list):
                # Extend current vector
                for item in new:
                    self.add(item)
            else:
                # Just append value to vector
                self.items.append(new)
        elif self.items != None:        
            if isinstance(self.items, int):
                if isinstance(new, int):
                    if (self.items-new) == 1:
                        self.items = (new, self.items)
                        return
                    elif (self.items-new) == -1:
                        self.items = (self.items, new)
                        return
            self.items = [self.items]
            self.add(new)
        else:
            self.items = new

    def intersection(self, second):
        first = set( self.values() ) 
        second = set( second.values() )
        result = first.intersection(second)
        if 0 < len(result):
            result = list(result)
        else:
            result = None
        return IntValues(result)
