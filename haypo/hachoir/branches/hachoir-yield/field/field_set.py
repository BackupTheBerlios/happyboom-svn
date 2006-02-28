from event_handler import EventHandler
from field import Field
from indexed_dict import IndexedDict

class FieldDoesExist(KeyError):
    pass

class FieldSet(Field):
    """
    Ordered list of fields. Use operator [] to access fields using their
    name (field names are unique in a field set, but not in the whole
    document).
    """
    is_field_set = True

    def __init__(self, parent, name, stream, description=None):
        Field.__init__(self, parent, name, self, description=description)
        self.stream = stream
        self.fields = IndexedDict()
        self._event_handler = None
        self._field_generator = self.createFields()
        self._field_array_count = {}
        self._size = None
        self._total_field_size = 0
        self.endian = "!"
        if parent != None:
            self.root = parent.root
        else:
            self.root = self

    def __str__(self):
        return "(...)" 

    def _getDisplay(self):
        return "(...)" 
    display = property(_getDisplay)

    def raiseEvent(self, event_name, *args):
        if self._event_handler == None:
            return
        self._event_handler.raiseEvent(event_name, *args)

    def connect(self, event_name, handler):
        if self._event_handler == None:
            self._event_handler = EventHandler()
        self._event_handler.connect(event_name, handler)

    def __len__(self):
        return len(self.fields)

    def _getSize(self):
        if self._size == None:
            self._feedAll()
        return self._size
    size = property(_getSize)

    def newFieldAskAddress(self):
        return self._total_field_size

    def _feed(self):
        # Instanciate the field
        stream_address = self.absolute_address + self._total_field_size
        field = self._field_generator.next()

        if False:
            addr = field.absolute_address
            print "* Instanciate %s (addr=%s.%s, size=%s bits)" \
                % (field.path, addr/8, addr%8, field.size)

        # Compute field address and total field size
        assert field.address == self._total_field_size
        self._total_field_size += field.size

        # Replace "name[]" with "name[<index>]"
        if field._name[-2:] == "[]":
            name = field._name[:-2]
            if name in self._field_array_count:
                self._field_array_count[name] += 1
            else:
                self._field_array_count[name] = 0
            field._name = name + "[%u]" % self._field_array_count[name]

        # Append field to the field list
        self.fields.append(field._name, field)
        return field

    def __getitem__(self, name):
        """
        Get an item with it's name or it's path.
        @rtype Field
        """
        
        # Get item with a path? (eg. "point/x")
        if "/" in name:
            path = name
            names = path.split("/")
            field = self
            for name in names:
                if name=="" or not field.is_field_set:
                    raise FieldDoesExist("Field '%s' doesn't exist in %s" \
                        % (path, self.path))
                field = field[name]
            return field

        # Field does exit?
        if name in self.fields:
            return self.fields[name]
            
        # Feed until field can be found
        if self._field_generator != None:
            field = self._feedUntil(name)
            if field != None:
                return field
        raise FieldDoesExist("Field '%s' doesn't exist in %s" \
            % (name, self.path))

    def __contains__(self, name):
        if "/" in name:
            names = name.split("/")
            field = self
            for name in names:
                if name=="" or not field.is_field_set:
                    return False
                field = field[name]
            return True
        else:
            if self._field_generator != None:
                field = self._feedUntil(name)
            return name in self.fields

    def _stopFeeding(self):
        self._field_generator = None
        self._size = self._total_field_size

    def _feedUntil(self, field_name):
        try:
            while True:
                field = self._feed()
                if field.name == field_name:
                    return field
        except StopIteration:
            self._stopFeeding()
        return None

    def _feedAll(self):
        try:
            while True:
                self._feed()
        except StopIteration:
            self._stopFeeding()

    def __iter__(self):
        if self._field_generator != None:
            self._feedAll()
        return iter(self.fields)

    def createFields(self):
        raise NotImplementedError

