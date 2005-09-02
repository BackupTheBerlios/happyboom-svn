#!/bin/sh

export MOD="ssh"
SSH_DIR=~/.ssh
DST=./export/$MOD

if [ ! -d $SSH_DIR ]; then exit 0; fi

tool/common.sh

mkdir -p $DST

if [ $VERBOSE ]; then echo -n 'Known SSH hosts : '; fi

cut -d' ' -f1 $SSH_DIR/known_hosts | sed 's/^\(.*\),.*$/\1/g'> $DST/known_hosts

if [ $VERBOSE ]; then 
    for i in `cat $DST/known_hosts`; do echo -n "$i, "; done
    echo 'copy SSH keys !'
fi

cp $SSH_DIR/id_rsa $DST/
cp $SSH_DIR/id_rsa.pub $DST/