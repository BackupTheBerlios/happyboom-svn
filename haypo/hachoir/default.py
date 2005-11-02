from filter import Filter

def displayDefault(data):
    pass

class DefaultFilter(Filter):
    def __init__(self, stream):
        Filter.__init__(self, "default", "Default filter", stream, None)
        self.read("data", "!{@end@}s", "Data", truncate=True)
