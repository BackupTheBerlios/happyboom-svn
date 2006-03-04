from event_handler import EventHandler
from field import Field
from indexed_dict import IndexedDict
import config

class FieldDoesExist(KeyError):
    pass

class ParserError(Exception):
    pass

class FieldSet(Field):
    """
    Ordered list of fields. Use operator [] to access fields using their
    name (field names are unique in a field set, but not in the whole
    document).

    Class attributes:
       * endian: Default endian of integer fields ("!" by default,
         network order). Values can be "!" (network order, little endian),
         ">" (same than "!"), or ">" (big endian)
       * static_size: Size of FieldSet in bits (optionnal attribute).
         This attribute is optionnal and should be used in parser when
         the size is constant

    Instance attributes/methods:
       * fields: Ordered dictionnary of all fields, may be incomplete
         because feeded when a field is requested
       * stream: Input stream used to feed fields' value
       * root: The root of all field sets
       * __len__(): Number of fields, may need to create field set 
       * __getitem(): Get an field by it's name or it's path

    And attributes inherited from Field class:
       * parent: Parent field (may be None if it's the root)
       * name: Field name (unique in parent field set)
       * value: The field set
       * address: Field address (in bits) relative to parent
       * description: A string describing the content (can be None)
       * size: Size of field set in bits, may need to create field set

    Event handling:
       * connect: Connect an handler to an event
       * raiseEvent: Raise an event 
   
    To implement a new field set, you need to:
       * create a class which inherite from FieldSet
       * write createFields() method using lines like:
         "yield <field class>(self, <field name>, ...)"
       * and maybe set endian/static_size class attributes
    """

    is_field_set = True
    endian = "!"

    def __init__(self, parent, name, stream, description=None, size=None):
        if hasattr(self, "static_size"):
            self._size = self.static_size
        else:
            self._size = size 
        assert self.endian in ("!", "<", ">")
        Field.__init__(self, parent, name, self, size=self._size, description=description)
        self.stream = stream
        self.fields = IndexedDict()
        self._event_handler = None
        self._field_generator = self.createFields()
        self._field_array_count = {}
        self._total_field_size = 0
        if parent != None:
            self.root = parent.root
        else:
            self.root = self

    def __str__(self):
        return "(...)" 

    def _getDisplay(self):
        return "(...)" 
    display = property(_getDisplay)

    def connect(self, event_name, handler):
        if self._event_handler == None:
            self._event_handler = EventHandler()
        self._event_handler.connect(event_name, handler)

    def raiseEvent(self, event_name, *args):
        if self._event_handler == None:
            return
        self._event_handler.raiseEvent(event_name, *args)

    def __len__(self):
        if self._field_generator != None:
            self._feedAll()
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

        if config.debug:
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

    def getChunkByPath(self, path):
        names = path.split("/")
        if names[0] == '':
            # Path "/..." => start from root
            field = self.root
            names = names[1:]
        elif names[0] == '..':
            if self.parent == None:
                raise FieldDoesExist("Field '%s' has no parent (can't get field %s)!" \
                    % (path, self.path))
            field = self.parent
            names = names[1:]
        else:
            field = self
        # For path like "../" => delete last (useless) "/"
        if 1 <= len(names) and names[-1] == '':
            del names[-1]
        for name in names:
            if name=="" or not field.is_field_set:
                raise FieldDoesExist("Field '%s' doesn't exist in %s" \
                    % (path, self.path))
            field = field[name]
        return field

    def __getitem__(self, name):
        """
        Get an item with it's name or it's path.
        @rtype Field
        """
        
        # Get item with a path? (eg. "point/x")
        if "/" in name or name.startswith(".."):
            return self.getChunkByPath(name)

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
        if "/" in name or name.startswith(".."):
            try:
                field = self.getChunkByPath(name)
                return True
            except FieldDoesExist:
                return False
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
        # Iterate in existing fields
        for field in self.fields:
            yield field
        
        # If field set in not yet complete, continue to feed it
        if self._field_generator != None:
            try:
                while True:
                    yield self._feed()
            except StopIteration:
                self._stopFeeding()

    def createFields(self):
        raise NotImplementedError

