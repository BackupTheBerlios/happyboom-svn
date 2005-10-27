#!/bin/sh

export MOD=yafc
IN=~/.yafc/bookmarks

if [ ! -e $IN ]; then exit 0; fi

tool/common.sh

tool/yafc.pl $IN
