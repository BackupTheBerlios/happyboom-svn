#!/bin/sh
PKG="happyboom"
VERSION="0.1.3"
FILES="ChangeLog README"
OUT="$PKG-$VERSION.tar.bz2"
TMP_DIR="$PKG-$VERSION"

rm -rf $TMP_DIR
mkdir $TMP_DIR

for i in $(find . -name "*.py" -o -name "*.sh"; echo $FILES); do
	FILE=$(echo $i | sed -e 's!\./!!')
	SUBDIR=$(dirname "$TMP_DIR/$FILE")
	test -d "$SUBDIR" || mkdir -p $SUBDIR
	ln $PWD/$FILE $TMP_DIR/$FILE
done

tar --create  --bzip --dereference --file $OUT $TMP_DIR	
rm -rf $TMP_DIR
