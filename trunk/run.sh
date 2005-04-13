xterm -e "cd $PWD; python server.py" &
sleep 1
xterm -e "cd $PWD; python view.py" &
xterm -e "cd $PWD; python input.py" &
