#!/bin/bash
export MOD=pypi
IN=~/.pypirc
if [ ! -e $IN ]; then exit 0; fi
tool/common.sh
echo "Pypi at http://cheeseshop.python.org/ -- $(grep username $IN) -- $(grep password $IN)"
