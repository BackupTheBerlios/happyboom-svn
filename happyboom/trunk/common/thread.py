import traceback, sys

def getBacktrace():
    bt = traceback.format_exception( \
        sys.exc_type, sys.exc_value, sys.exc_traceback)
    return "".join(bt)
