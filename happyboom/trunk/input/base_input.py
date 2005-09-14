import time
import string
import os
import signal
from net import io
from net import io_udp
#from net import io_tcp
from net import net_buffer
import thread

class BaseInput(object):
    def __init__(self):
        self.__io = io_udp.IO_UDP() 
        #self.__io = io_tcp.IO_TCP() 
        self.pid = os.getpid()
        self.quit = False
        self.active = True
        self.debug = False
        self.verbose = False
        self.cmds = None
        self.use_readline = False
        self.__protocol_version = "0.1.4"
        self.name = "-"
        self.__recv_buffer = net_buffer.NetBuffer()

    def processPacket(self, new_packet):
        self.__recv_buffer.append(0,new_packet.data)
    
    def readCmd(self, timeout=1.000):
        return self.__recv_buffer.readBlocking(0,timeout)
    
    def serverChallenge(self):
        if self.verbose: 
            print "Start server challenge (send version, send name, ...)."

        cmd = self.readCmd()
        if cmd==None: return False
        if cmd != "Version?": 
            if self.debug: print "Server answer: %s instead of Version?" % (cmd)
            return False
        self.sendCmd(self.__protocol_version)
        
        cmd = self.readCmd()
        if cmd==None: return False
        if cmd != "OK":
            if self.debug: print "Server answer: %s instead of OK" % (cmd)
            return False
        
        cmd = self.readCmd()
        if cmd==None: return False
        if cmd != "Name?":
            if self.debug: print "Server answer: %s instead of Name?" % (cmd)
            return False
        self.sendCmd(self.name)

        if self.debug: print "Challenge: Wait Name OK"
        cmd = self.readCmd()
        if cmd==None: return False
        if cmd != "OK":
            if self.debug: print "Server answer: %s instead of OK" % (cmd)
            return False
        if self.verbose: print "Server challenge done."
        return True

    def start(self, host, port):
        # Try to connect to server
        if self.verbose: 
            print "Try to connect to server %s:%s" % (host, port)
        self.__io.on_disconnect = self.onDisconnect
        self.__io.on_lost_connection = self.onLostConnection
        self.__io.on_new_packet = self.processPacket
        self.__io.connect(host, port)

        thread.start_new_thread( self.__io.run_thread, ())

        # Server "challenge" (version, name, ...)
        if self.serverChallenge() != True:
            if not self.quit:
                print "Server communication mistake !?"
            self.stop()
            return

        thread.start_new_thread( self.runIo, ())

    def setDebugMode(self, debug):
        self.debug = debug
        self.__io.debug = debug

    def setVerbose(self, verbose):
        self.verbose = verbose
        self.__io.verbose = verbose

    def sendCmd(self, cmd):
        self.__io.send( io.Packet(cmd))

    def processCmd(self, cmd):
        if cmd != "": self.sendCmd(cmd)

    def runIo(self):
        while 1:
            cmd = self.__recv_buffer.readNonBlocking(0)
            while cmd != None:
                if cmd == "quit":
                    self.stop()
                    break
                cmd = self.__recv_buffer.readNonBlocking(0)
            time.sleep(0.250)
    
    def live(self):
        if self.use_readline: import readline
        while self.quit == False:
            cmd = raw_input("cmd ? ")
            if cmd != "":
                self.processCmd(cmd)
            if (cmd == "quit") or (cmd == "close"):
                self.quit = True

    def onDisconnect(self):
        print "Disconnect from server."
        self.stop()

    def onLostConnection(self):
        print "Lost connection with server."
        self.stop()

    def stop(self):
        if not self.active: return
        self.active = False
        self.quit = True
        self.__io.stop()
        print "Input closed."
