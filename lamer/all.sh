#!/bin/sh
for i in `find ./ -maxdepth 1 -type f -perm -700 -name 'mod_*' | grep -v '~'`; do
  ./$i
done
