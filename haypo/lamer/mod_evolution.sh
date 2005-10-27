#!/bin/bash

export MOD=evolution
IN=~/.gnome2_private/Evolution
if [ ! -e $IN ]; then exit 0; fi

tool/common.sh

tool/evolution.pl $IN

