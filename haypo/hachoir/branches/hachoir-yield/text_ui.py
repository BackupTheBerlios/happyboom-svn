def displayFieldSet(field_set, max_depth=2, depth=0):
    parent_details = False
    display_bits = False
    indent = " " * (3*depth)
    addr = field_set.absolute_address
    text = "%s--- %s ---" % (indent, field_set.name) 
    if parent_details:
        if display_bits:
            text += "(addr=%u.%u, size=%s bits)" \
                % (addr/8, addr%8, field_set.size)
        else:
            assert (addr % 8) == 0
            assert (field_set.size % 8) == 0
            text += "(addr=%u, size=%s bytes)" \
                % (addr/8, field_set.size/8)
    print text
    if max_depth == None or depth < max_depth:
        for field in field_set:
            if not field.is_field_set:
                text = indent
                if display_bits:
                    text += "%u.%u" % (field.address/8, field.address%8)
                else:
                    assert (field.address % 8) == 0
                    text += "%u" % (field.address/8)
                text += ") %s = %s (%s)" % \
                    (field._name, field.display, field.description)
                if display_bits:
                    text += "(size=%s bits)" % field.size
                else:
                    assert (field.size % 8) == 0
                    text += "(size=%s bytes)" % (field.size / 8)
            else:
                displayFieldSet(field, max_depth, depth+1)
    else:
        print "%s(...)" % indent
    if depth == 0:
        print

