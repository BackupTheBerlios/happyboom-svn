import traceback, sys, string, re

def _regexMaxLength(pattern, in_parenthesis=False):
    """
    Don't use this function directly, use regexMagLength!
    """

    re_letter = re.compile( r"^[^][()|.?+*{}](.*)$")
    re_set = re.compile( r"^\[" + r"[^]]*" + r"\](.*)$" )
    re_min_repetition = re.compile( r"^\{([0-9]+)\}(.*)$" )
    re_min_max_repetition = re.compile( r"^\{([0-9]+),([0-9]+)\}(.*)$" )

    size = 0
    atom_size = 0
    state = 0 # get atom
    is_end = len(pattern) == 0
    if in_parenthesis and not is_end:
        is_end = pattern[0] in ("|", ")")
    while not is_end:
        if state==0:
            size = size + atom_size

            # Pattern: [...] => size=1
            if pattern[0] == '(':
                pattern = pattern[1:]
                atom_size = None
                while True:
                    tmp_atom_size, pattern = _regexMaxLength(pattern, True)
                    if tmp_atom_size == None:
                        return None, pattern
                    if atom_size==None or atom_size<tmp_atom_size:
                        atom_size = tmp_atom_size
                    if pattern[0] == ')':
                        break
                    assert pattern[0] == '|'
                    pattern = pattern[1:]
                pattern = pattern[1:]
            else:
                m = re_set.match(pattern)
                if m != None:
                    pattern = m.group(1)
                    atom_size = 1
                else:
                    m = re_letter.match(pattern)
                    if m == None:
                        return (-1, pattern,)
                    atom_size = 1
                    pattern = m.group(1)
            state = 1                
        else:
            assert state==1

            # Repetiton: + or * => no limit
            if pattern[0] in ("*", "+"):
                return (None, pattern,)
            
            # Repetition: {2}
            m = re_min_repetition.match(pattern)
            if m != None:
                repetition = int(m.group(1))
                print "(rep=%sx%s)" % (atom_size, repetition)
                pattern = m.group(2)
                atom_size = atom_size * repetition
            else:
                # Repetition: {1,2}
                m = re_min_max_repetition.match(pattern)
                if m != None:
                    repetition = int(m.group(2))
                    pattern = m.group(3)
                    atom_size = atom_size * repetition
            state = 0

        is_end = len(pattern) == 0
        if in_parenthesis and not is_end:
            is_end = pattern[0] in ("|", ")")

    return (size + atom_size, pattern,)

def regexMaxLength(pattern):
    """
    Get maximum size of a regular expression pattern.
    Returns (size, pattern). If size=-1, an error occurs (pattern contains
    the buggy pattern). If size=-1, no limit does exist.
    """

    size, pattern = _regexMaxLength(pattern)
    if size == -1:
        raise "Can't parse regular expression: %s" % pattern 
    return size 

def humanDuration(ms):
    if ms < 1000:
        return "%u ms" % ms
    sec = ms/1000
    ms = ms%1000
    if sec < 60:
        return  "%u sec" % sec
    min = sec/60
    sec = sec%60
    text = "%u min %u sec" % (min, sec)
    return text

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

def convertDataToPrintableString(data, keep_n=False):
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
                if not keep_n or c != "\n":
                    display = display + know[c]
                else:
                    display = display + c
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
