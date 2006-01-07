#!/bin/sh

export MOD=gftp
IN=~/.gftp/bookmarks
DIR=$(dirname $0)
DESCRAMBLE=tool/gftp_descramble

if [ ! -e $IN ]; then exit 0; fi
cd $DIR
if [ ! -e $DESCRAMBLE ]; then
  if [ $VERBOSE ]; then echo "(call make)"; fi
  make
fi

tool/common.sh
tool/gftp_bookmark.pl $IN
