#!/bin/bash

export MOD=ncftp
IN=~/.ncftp/bookmarks

if [ ! -e $IN ]; then exit 0; fi
tool/common.sh

tail -n +3 $IN | tool/ncftp_bookmark.pl
