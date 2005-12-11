from filter import Filter

class EmptyFilter(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "empty", "Empty filter", stream, parent)

class DefaultFilter(Filter):
    def __init__(self, stream, parent=None):
        Filter.__init__(self, "default", "Default filter", stream, parent)
        self.read("data", "!{@end@}s", "Data")
