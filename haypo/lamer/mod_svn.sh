#!/bin/bash
export MOD=svn
IN=~/.subversion/auth
if [ ! -d $IN ]; then exit 0; fi
tool/common.sh
for filename in $(ls $IN/svn.simple/*); do
  tool/parse_svn_simple.py $filename;
done
