PACKAGE=hachoir
VERSION=2005-12-26
ARCHIVE=$PACKAGE-$VERSION.tar.bz2
TMP_DIR=/tmp
DIR=$PWD
if [ -e $TMP_DIR/$PACKAGE ]; then
        rm -rf $TMP_DIR/$PACKAGE
fi

echo "* Export data"
svn export . $TMP_DIR/$PACKAGE

echo "* Create $ARCHIVE"
(cd $TMP_DIR && tar cjf $DIR/$ARCHIVE $PACKAGE)

echo "$DIR/$ARCHIVE wrote."
