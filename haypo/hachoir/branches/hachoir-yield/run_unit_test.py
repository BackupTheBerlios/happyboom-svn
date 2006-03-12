from unit_test import (create_fields, 
    field_set_get_item, stream_search, output_stream)
import sys, os

def runAllTests():
    create_fields.runTests()
    field_set_get_item.runTests()
    stream_search.runTests()
    output_stream.runTests()

def main():
    # Load Hachoir library
    current_dir = os.path.dirname(__file__)
    libhachoir_path = os.path.join(current_dir, "libhachoir")
    sys.path.append(libhachoir_path)

    # Run tests
    runAllTests()

if __name__ == "__main__":
    main()

