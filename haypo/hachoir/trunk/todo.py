def todoWriteMethod(obj, method):
    raise Exception("Class %s doesn't implement method %s!" % (obj.__class__.__name__, method))
