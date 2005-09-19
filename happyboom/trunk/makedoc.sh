#!/bin/sh
test -e doc || mkdir doc
epydoc \
    -o doc/api \
    -n "HappyBoom game engine 0.2" \
    --private-css blue \
    common net server
