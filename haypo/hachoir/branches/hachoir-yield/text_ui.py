def displayFieldSet(field_set, max_depth=2, depth=0):
    parent_details = False
    indent = " " * (3*depth)
    addr = field_set.absolute_address
    text = "%s--- %s ---" % (indent, field_set.name) 
    if parent_details:
        text += "(addr=%u.%u, size=%s bits)" \
            % (addr/8, addr%8, field_set.size)
    print text
    if max_depth == None or depth < max_depth:
        for field in field_set:
            if not field.is_field_set:
                print "%s%u.%u) %s = %s (%s) (size=%s bits)" % \
                    (indent, field.address/8, field.address%8, field._name, field.display, field.description, field.size)
            else:
                displayFieldSet(field, max_depth, depth+1)
    else:
        print "%s(...)" % indent
    if depth == 0:
        print

