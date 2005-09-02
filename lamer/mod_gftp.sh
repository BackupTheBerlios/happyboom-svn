#!/bin/sh

export MOD=gftp
DST=export/
mkdir -p $DST
IN=~/.gftp/bookmarks

if [ ! -e $IN ]; then exit 0; fi

tool/common.sh

tool/gftp_bookmark.pl $IN | tee $DST/$MOD
