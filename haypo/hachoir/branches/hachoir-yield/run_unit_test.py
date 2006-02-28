from unit_test import create_fields
from unit_test import field_set_get_item

def runAllTests():
    create_fields.runTests()
    field_set_get_item.runTests()

if __name__ == "__main__":
    runAllTests()
