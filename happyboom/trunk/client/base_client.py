from net import io_udp
import struct

class HappyBoomClient(object):
    
    def __init__(self, args):
        self.host = args.get("host", "127.0.0.1")
        self.port = args.get("port", "12430")
        self.verbose = args.get("verbose", False)
        self.debug = args.get("debug", False)
        protocol = args.get("protocol", None)
        self.__io = io_udp.IO_UDP()
        self.__verbose = verbose
        self.__io.verbose = verbose
        self.__debug = debug
        self.__io.debug = debug
        self.__stopped = False
        self.__stoplock = thread.allocate_lock()
        
        self.signature = None
        self.gateway = Gateway(self.__io, protocol)
        
    def start(self):
        """ Starts the client : connection to the server, etc. """
        # Try to connect to server
        if self.__verbose: print "[HAPPYBOOM] Trying to connect to server %s:%u" % (self.host, self.port)
        self.__io.on_connect = self.onConnect
        self.__io.on_connection_fails = self.onConnectionFails
        self.__io.on_disconnect = self.onDisconnect
        self.__io.on_new_packet = self.gateway.processPacket
        self.__io.on_lost_connection = self.onLostConnection
        self.__io.connect(self.host, self.port)
        if not self.__io.is_ready: return
        thread.start_new_thread(self.__io.run_thread, ())
        
    def stop(self):
        """ Stops the display client : disconnection from the server, etc. """
        # Does not stop several times
        self.__stoplock.acquire()
        if self.__stopped:
            self.__stoplock.release()
            return
        self.__stopped = True
        self.__stoplock.release()
        
        self.send("quit")
        self.__io.stop()
        if self.__verbose: print "[HAPPYBOOM] Stopped"
        
    def __isStopped(self):
        self.__stoplock.acquire()
        stop = self.__stopped
        self.__stoplock.release()
        return stop
    stopped = property(__isStopped)
    
    def onConnect(self):
        """ Handler called on network connection. """
        if self.__verbose: print "[HAPPYBOOM] Connected to server"
        
    def onConnectionFails(self):
        """ Handler called when network connection fails. """
        print "[HAPPYBOOM] Fail to connect to the server"

    def onDisconnect(self):
        """ Handler called on network disconnection. """
        print "[HAPPYBOOM] Connection to server closed"
        self.launchEvent("happyboom", "stop")

    def onLostConnection(self):
        """ Handler called on losting network connection. """
        print "[HAPPYBOOM] Lost connection with server"
        self.launchEvent("happyboom", "stop")
        
    def processPacket(self, new_packet):
        """ Processes incomming network packets (converts and launches local event).
        @param new_packet: incomming network packet.
        @type new_packet: C{net.io.packet.Packet}
        """
        event_type, arg = self.str2evt(new_packet.data)
        if event_type != None: 
            if self.__debug: print "Received message: type=%s arg=%s" %(event_type, arg)
            self.launchEvent(event_type, arg)
            
    def send(self, str):
        """ Sends a string to the network server.
        @param str: String to send.
        @type str: C{str}
        """
        p = io.Packet()
        p.writeStr(str)
        self.__io.send(p)
        


