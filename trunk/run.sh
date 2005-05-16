#!/bin/sh
xterm -e "cd $PWD; python console_server.py" &
sleep 1
xterm -e "cd $PWD; python console_view.py" &
xterm -e "cd $PWD; python console_input.py" &
