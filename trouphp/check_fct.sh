#!/bin/sh

DIR=$(dirname $0)

# Check source file
if [ $# -lt 2 ]; then
  echo "$(basename $0) file.php check1 check2 ... : List all functions with match with given regex"
  echo
  echo "Available checks :"
  for i in $(cd $DIR; ls *.regex); do
     echo "· $i"
  done
  exit 1
fi
SRC=$1
shift

if [ ! -e $SRC ]; then
	echo "PHP source file \"$SRC\" doesn't exist";
fi

GREP_OPT="-H -n"

for i in $*; do
  FILE="$DIR/$i.regex"
  if [ -e $FILE ]; then
    REGEX_FUNC=$(cat $FILE);
    egrep $GREP_OPT "$REGEX_FUNC" $SRC;
  else
    echo "File $FILE doesn't exist";
  fi
done
