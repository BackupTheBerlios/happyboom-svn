import traceback, sys
import string

def humanFilesize(size):
    if size < 1000:
        return "%u bytes" % size
    units = ["KB", "MB", "GB"]
    size = float(size)
    for unit in units:
        size = size / 1024
        if size < 100:
            return "%.1f %s" % (size, unit)
        if size < 1000:
            return "%u %s" % (size, unit)
        last_unit = unit
    return "%u %s" % (size, unit)

def convertDataToPrintableString(data):
    if len(data) == 0:
        return "(empty)"
    display = ""
    for c in data:
        if ord(c)<32:
            know = { \
                "\n": "\\n",
                "\r": "\\r",
                "\t": "\\t",
                "\0": "\\0"}
            if c in know:
                display = display + know[c]
            else:
#                display = display + "\\x%02X" % ord(c)
                display = display + "."
        elif c in string.printable:
            display = display + c
        else:
            display = display + "."
    return "\"%s\"" % display

def getBacktrace():
    try:
        bt = traceback.format_exception( \
            sys.exc_type, sys.exc_value, sys.exc_traceback)
        return "".join(bt)
    except:
        return "Error while trying to get backtrace"
