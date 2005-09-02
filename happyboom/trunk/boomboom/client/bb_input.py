"""
@author: Victor Stinner and Damien Boucard
@license: Gnu/GPL v2 or later, see LICENSE file.
@contact: See U{http://developer.berlios.de/projects/happyboom/}
@version: 0.2
"""
from common import simple_event
from common.simple_event import EventLauncher
import bb_events
from net import io
from net import io_udp, io_tcp
from net import net_buffer
import thread, time, pygame

class BoomBoomInput(EventLauncher):
    """ Class which manages "input" part of the network connections.
    @ivar host: Server hostname.
    @type host: C{str}
    @ivar port: Server port for "input" connection.
    @type port: C{int}
    @ivar name: Name of the client (as known by the server).
    @type name: C{str}
    @ivar __protocol_version: Current version of the protocol used by the client.
    @type __protocol_version: C{str}
    @ivar __io: Network input/output object using UDP protocole.
    @type __io: C{net.io_udp.IO_UDP}
    @ivar __recv_buffer: Network data reception buffer.
    @type __recv_buffer: C{net.net_buffer.NetBuffer}
    @ivar __verbose: Verbose mode flag.
    @type __verbose: C{bool}
    @ivar __debug: Debug mode flag.
    @type __debug: C{bool}
    @ivar __stopped: Stopped input client flag.
    @type __stopped: C{bool}
    @ivar __stoplock: Mutex for synchronizing __stopped.
    @type __stoplock: C{thread.lock}
    """
    
    def __init__(self, host, port=12431, name="-", verbose=False, debug=False):
        """ BoomBoomInput constructor.
        @param host: Server hostname.
        @type host: C{str}
        @param port: Server port for "input" connection.
        @type port: C{int}
        @param name: Name of the client (as known by the server).
        @type name: C{string}
        @param verbose: Verbose mode flag.
        @type verbose: C{bool}
        @param debug: Debug mode flag.
        @type debug: C{bool}
        """
        EventLauncher.__init__(self)
        self.host = host
        self.port = port
        self.name = name
        self.__io = io_tcp.IO_TCP()
        self.__recv_buffer = net_buffer.NetBuffer()
        self.__verbose = verbose
        self.__io.verbose = verbose
        self.__debug = debug
        self.__io.debug = debug
        self.__protocol_version = "0.1.4"
        self.__stopped = False
        self.__stoplock = thread.allocate_lock()
        
    def start(self):
        """ Starts the input client : connection to the server, etc. """
        # Try to connect to server
        if self.__verbose: print "[INPUT] Trying to connect to server %s:%s" % (self.host, self.port)
        self.__io.on_connect = self.onConnect
        self.__io.on_disconnect = self.onDisconnect
        self.__io.on_lost_connection = self.onLostConnection
        self.__io.on_new_packet = self.processPacket
        self.__io.connect(self.host, self.port)
        thread.start_new_thread( self.__io.run_thread, ())
        
        stopped = False
        # Server "challenge" (version, name, ...)
        if self.serverChallenge() != True:
            self.__stoplock.acquire()
            stopped = self.__stopped
            self.__stoplock.release()
            if not stopped:
                print "[INPUT] Server communication mistake !?"
                self.launchEvent(bb_events.stop)
            return

        thread.start_new_thread(self.runIo, ())
        
        while not stopped:
            for input_event in pygame.event.get():
                self.process_event(input_event)
            time.sleep(0.020)
            self.__stoplock.acquire()
            stopped = self.__stopped
            self.__stoplock.release()
        
    def stop(self):
        """ Stops the input client : disconnection from the server, etc. """
        self.__stoplock.acquire()
        self.__stopped = True
        self.__stoplock.release()
        self.__io.stop()
        if self.__verbose: print "[INPUT] Stopped"
        
    def processPacket(self, new_packet):
        """ Bufferizes incomming packets.
        @param new_packet: Incomming network packet.
        @type new_packet: C{net.io.packet.Packet}
        """
        self.__recv_buffer.append(0,new_packet.data)
    
    def readCmd(self, timeout=1.000):
        """ Reads incomming commands via the reception buffer.
        @param timeout: Timeout to unblock the function.
        @type timeout: C{float}
        @return: Command read if timeout didn't perform.
        @rtype: C{str}
        """
        return self.__recv_buffer.readBlocking(0,timeout)
        
    def sendCmd(self, cmd):
        """ Sends a command to the network server.
        @param cmd: Command to send.
        @type cmd: C{str}
        """
        self.__io.send(io.Packet(cmd))
        
    def processCmd(self, cmd):
        """ Sends only non empty-string command.
        @param cmd: Command to send.
        @type cmd: C{str}
        """
        if cmd != "": self.sendCmd(cmd)
        
    def serverChallenge(self):
        """ Negociate initialisation with the network server. """
        if self.__verbose: print "[INPUT] Start server challenge (send version, send name, ...)."

        cmd = self.readCmd()
        if cmd==None: return False
        if cmd != "Version?": 
            if self.__debug: print "[INPUT] Server answer: %s instead of Version?" % (cmd)
            return False
        self.sendCmd(self.__protocol_version)
        
        cmd = self.readCmd()
        if cmd==None: return False
        if cmd != "OK":
            if self.__debug: print "[INPUT] Server answer: %s instead of OK" % (cmd)
            return False
        
        cmd = self.readCmd()
        if cmd==None: return False
        if cmd != "Name?":
            if self.__debug: print "[INPUT] Server answer: %s instead of Name?" % (cmd)
            return False
        self.sendCmd(self.name)

        if self.__debug: print "[INPUT]Challenge: Wait Name OK"
        cmd = self.readCmd()
        if cmd==None: return False
        if cmd != "OK":
            if self.__debug: print "[INPUT] Server answer: %s instead of OK" % (cmd)
            return False
        if self.__verbose: print "[INPUT] Server challenge done successfully"
        return True
        
    def runIo(self):
        """ Waits for a quit command from server. """
        while 1:
            cmd = self.__recv_buffer.readNonBlocking(0)
            while cmd != None:
                if cmd == "quit":
                    self.launchEvent(bb_events.stop)
                    break
                cmd = self.__recv_buffer.readNonBlocking(0)
            time.sleep(0.250)
            
    def onConnect(self):
        """ Handler called on network connection. """
        if self.__verbose: print "[INPUT] Connected to server"
            
    def onDisconnect(self):
        """ Handler called on network disconnection. """
        print "[INPUT] Disconnected from server"
        self.launchEvent(bb_events.stop)

    def onLostConnection(self):
        """ Handler called on losting network connection. """
        print "[INPUT] Lost connection with server"
        self.launchEvent(bb_events.stop)
            
    def process_event_active(self, event):
        """ Manages when a pygame event is caught and interact with the server.
        @param event: Pygame event.
        @type event: C{pygame.Event}
        """
        #delta_angle = -30
        if event.type == pygame.KEYDOWN: 
            # arrow keys: move character
            if event.key == 32: self.sendCmd("shoot")
            elif event.key == 275: self.sendCmd("move_right")
            elif event.key == 273: self.sendCmd("move_up") 
            elif event.key == 274: self.sendCmd("move_down")
            elif event.key == 276: self.sendCmd("move_left")

    def process_event(self, event):
        """ Manages when a pygame event is caught.
        @param event: Pygame event.
        @type event: C{pygame.Event}
        """
        if event.type == pygame.KEYDOWN: 
            # q, Q or escape: quit
            if event.unicode in (u'q', u'Q') or event.key == 27:
                self.launchEvent(bb_events.stop)
        # Quit event: quit
        elif event.type in (pygame.QUIT, ):
            self.launchEvent(bb_events.stop)
    
        #character = self.client.view.getActiveCharacter()
        #if character != None: self.process_event_active(character, event)
        self.process_event_active(event)