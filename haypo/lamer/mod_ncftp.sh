#!/bin/bash

export MOD=ncftp
IN=~/.ncftp/bookmarks

if [ ! -e $IN ]; then exit 0; fi

DIR=$(dirname $0)
$DIR/tool/common.sh
tail -n +3 $IN | $DIR/tool/ncftp_bookmark.pl
