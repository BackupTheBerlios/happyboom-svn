#!/bin/sh

export MOD=yafc
IN=~/.yafc/bookmarks
if [ ! -e $IN ]; then exit 0; fi
DIR=$(dirname $0)

cd $DIR
tool/common.sh
tool/yafc.pl $IN
