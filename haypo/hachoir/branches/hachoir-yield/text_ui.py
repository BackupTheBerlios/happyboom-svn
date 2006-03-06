def displayFieldSet(field_set, max_depth=2, depth=0, options={}):
    display_parent_addr = options.get("parent-addr", False)
    display_parent_size = options.get("parent-size", True)
    indent = " " * (3*depth)
    addr = field_set.absolute_address
    text = "%s--- %s ---" % (indent, field_set.name) 
    if display_parent_addr or display_parent_size:
        display_bits = (addr % 8) != 0 or (field_set.size % 8) != 0 
        info = []
        if display_bits:
            if display_parent_addr:
                info.append( "addr=%u.%u" % (addr/8, addr%8) )
            if display_parent_size:
                info.append( "size=%s bits" % field_set.size )
        else:
            assert (addr % 8) == 0
            assert (field_set.size % 8) == 0
            if display_parent_addr:
                info.append( "addr=%u" % (addr/8) )
            if display_parent_size:
                info.append( "size=%s bytes" % (field_set.size/8) )
        text += " (%s)" % (", ".join(info))
    print text
    if max_depth == None or max_depth < 0 or depth < max_depth:
        for field in field_set:
            if not field.is_field_set:
                display_bits = (field.address % 8) != 0 or (field.size % 8) != 0 
                text = indent
                if display_bits:
                    text += "%u.%u" % (field.address/8, field.address%8)
                else:
                    assert (field.address % 8) == 0
                    text += "%u" % (field.address/8)
                text += ") %s = %s: %s " % \
                    (field._name, field.display, field.description)
                if display_bits:
                    text += "(size=%s bits)" % field.size
                else:
                    assert (field.size % 8) == 0
                    text += "(size=%s bytes)" % (field.size / 8)
                print text
            else:
                displayFieldSet(field, max_depth, depth+1, options)
    else:
        print "%s(...)" % indent
    if depth == 0:
        print

