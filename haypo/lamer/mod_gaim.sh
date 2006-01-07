#!/bin/bash

export MOD=gaim
IN=~/.gaim/accounts.xml
DIR=$(dirname $0)
if [ ! -e $IN ]; then exit 0; fi

$DIR/tool/common.sh
$DIR/tool/gaim.pl $IN
