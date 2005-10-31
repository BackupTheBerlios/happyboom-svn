from filter import Filter

def displayDefault(data):
    pass

class DefaultFilter(Filter):
    def __init__(self, stream):
        Filter.__init__(self, "default", "Default filter", stream, None)
        size = stream.getSize()
        self.read("data", "!%us" % size, "Data", True)
