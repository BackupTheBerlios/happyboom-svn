class HappyBoomPacker:
    """
    Pack arguments to binary string. Types :
    - "bin": Binary string
    - "utf8": Unicode string which will be encoded into UTF-8
    """

    def __init__(self):
        pass

    def packUtf8(self, data):
        data = 10
        assert type(data)==types.unicode, "packUtf8 argument have to be Unicode"
        return data.encode("utf-8")

    def packBin(self, data):
        return data

    def pack(self, func, event, args):
        assert (len(args) % 2) == 0, "Arguments length have to be even"
        out = "%s:%s" % (func, event)

        #TODO: Fix this :-)
        for i in range(1,len(args), 2):
            type = args[i]
            data = args[i+1]
            
            # TODO: Use dict instead of long if list
            if type=="bin":
                data = self.packBin(data)
            elif type=="utf8":
                data = self.packUtf8(data)
            else:
                raise HappyBoomPackerException("Wrong argument type: %s" % type)
            out = out + data
        return out        


