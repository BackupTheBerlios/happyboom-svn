from filter import OnDemandFilter
from chunk import FormatChunk

#class EmptyFilter(OnDemandFilter):
#    def __init__(self, stream, parent=None):
#        OnDemandFilter.__init__(self, "empty", "Empty filter", stream, parent)

class DefaultFilter(OnDemandFilter):
    def __init__(self, stream, parent=None):
        OnDemandFilter.__init__(self, "default", "Default filter", stream, parent)
        self.read("data", "Raw data", (FormatChunk, "string[%u]" % stream.getSize()))
