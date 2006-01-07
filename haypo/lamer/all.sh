#!/bin/sh
DIR=$(dirname $0)
for i in `find $DIR -maxdepth 1 -type f -perm -700 -name 'mod_*' | grep -v '~'`; do
  $i
done
