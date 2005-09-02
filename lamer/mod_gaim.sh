#!/bin/bash

export MOD=gaim
IN=~/.gaim/accounts.xml
if [ ! -e $IN ]; then exit 0; fi

tool/common.sh

tool/gaim.pl $IN

