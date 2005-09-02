#!/bin/sh

export MOD=yafc
DST=export/
mkdir -p $DST
IN=~/.yafc/bookmarks

if [ ! -e $IN ]; then exit 0; fi

tool/common.sh

tool/yafc.pl $IN | tee $DST/$MOD
