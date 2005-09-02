#!/bin/sh

export MOD=gftp
DST=export/
mkdir -p $DST
IN=~/.gftp/bookmarks
DESCRAMBLE=tool/gftp_descramble

if [ ! -e $IN ]; then exit 0; fi
if [ ! -e $DESCRAMBLE ]; then
  if [ $VERBOSE ]; then echo "(call make)"; fi
  make
fi

tool/common.sh

tool/gftp_bookmark.pl $IN | tee $DST/$MOD
