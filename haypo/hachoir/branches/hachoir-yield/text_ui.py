def displayFieldSet(field_set, depth=0):
    indent = " " * (3*depth)
    addr = field_set.absolute_address
    print "%s--- %s --- (addr=%u.%u, size=%s bits)" \
        % (indent, field_set.name, addr/8, addr%8, field_set.size)
    for field in field_set:
        if not field.is_field_set:
            print "%s%u.%u) %s = %s (%s) (size=%s bits)" % \
                (indent, field.address/8, field.address%8, field._name, field.display, field.description, field.size)
        else:
            displayFieldSet(field, depth+1)
    if depth == 0:
        print

