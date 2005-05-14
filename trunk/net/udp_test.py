import getopt
from packet import Packet
from udp import IO_UDP
import thread
import sys
import re
import time

def loop_server(io):
	io.thread_sleep = 0.010
	thread.start_new_thread( io.run_thread, ())
	while 1:
		msg = raw_input(">> ")
		if msg=="": break
		packet = Packet()
		packet.writeStr(msg)
		io.send(packet)
		time.sleep(0.100)
		print ""
		
def loop_client(io):
	io.thread_receive = False
	thread.start_new_thread( io.run_thread, ())
	
	while 1:
		msg = raw_input(">> ")
		if msg=="": break
		
		m = re.compile("^eval:(.+)$").match(msg)
		if m != None: msg = eval(m.group(1))			
		
		packet = Packet()
		packet.writeStr(msg)
		if msg[0]=='0':			
			packet.skippable = True
		io.send(packet)
		io.thread_receive = True
		time.sleep(0.100)
		print ""

def main():
	is_server = False
	port = 12430
	host = "localhost"
	try:
		opts, args = getopt.getopt(sys.argv[1:], "", ["host=","server"])
	except getopt.GetoptError:
		print "Arguments parse error"

	for o, a in opts:
		if o == "--server":
			is_server = True
		if o in ("--host"):
			host = a
	
	# Create IO
	io = IO_UDP(is_server)
	io.debug = True
	port = 12430
	if is_server: host = ''
	io.connect(host, port)	

	# Main loop
	try:
		if is_server:
			loop_server(io)
		else:
			loop_client(io)
	except KeyboardInterrupt:
		io.stop()
		print "\nProgramme interrompu (CTRL+C)."
	
if __name__=="__main__": main()
