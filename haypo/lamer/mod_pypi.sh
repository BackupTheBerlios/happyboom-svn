#!/bin/bash
export MOD=pypi
IN=~/.pypirc
if [ ! -e $IN ]; then exit 0; fi
tool/common.sh
echo "http://cheeseshop.python.org/"
echo $(grep username $IN)
echo $(grep password $IN)
