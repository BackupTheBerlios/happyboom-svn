#!/bin/bash

export MOD=evolution
IN=~/.gnome2_private/Evolution
if [ ! -e $IN ]; then exit 0; fi
DIR=$(dirname $0)

$DIR/tool/common.sh
$DIR/tool/evolution.pl $IN
