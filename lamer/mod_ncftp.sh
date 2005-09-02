#!/bin/bash

export MOD=ncftp
DST_DIR=export/
mkdir -p $DST_DIR
IN=~/.ncftp/bookmarks

if [ ! -e $IN ]; then exit 0; fi
tool/common.sh

tail -n +3 $IN | tool/ncftp_bookmark.pl | tee $DST_DIR/$MOD
