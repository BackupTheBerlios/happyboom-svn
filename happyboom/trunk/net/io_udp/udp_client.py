from net import io
import thread
import time
import struct
from udp_ping import UDP_Pinger 

class UDP_Client(io.IO_Client):
    """ An UDP Client.
    @ivar __waitAck: List of packets (id) which are waiting for an acknoledge.
    @type __waitAck: C{dict<int>, L{Packet<io.Packet>}}
    @ivar __waitAck_sema: Lock used to access L{__waitAck}.
    @type __waitAck_sema: C{thread.lock}
    @ivar __received: List of received packets (id). List used to remove duplicated packets.
    @type __received: C{dict<int, L{Packet<io.Packet>}>}
    @ivar __received_sema: Lock used to access L{__received}.
    @type __received_sema: C{thread.lock}
    @ivar __pinger: Send regulary ping to server.
    @type __pinger: C{L{UDP_Pinger}}
    """
    def __init__(self, io_udp, addr, name=None):
        """ Constructor.
        @parameter io_udp: Main IO.
        @type io_udp: C{L{IO_UDP}}
        @parameter addr: The client network address (host, port).
        @type addr: C{(str, int)}
        @parameter name: The client name.
        @type name: C{str}
        """
        io.IO_Client.__init__(self, io_udp, addr, name)
        self.send_ping = False
        self.__waitAck = {}
        self.__received = {}
        self.__waitAck_sema = thread.allocate_lock()
        self.__received_sema = thread.allocate_lock()
        self.__pinger = UDP_Pinger(self)

    def alreadyReceived(self, id):
        """ Tell if a packet (id) is already received.
        @rtype: C{bool}
        """
        self.__received_sema.acquire()
        received = id in self.__received
        self.__received_sema.release()
        return received

    def receivePacket(self, packet):
        """ Process a new received packet.
        @type packet: C{L{Packet<io.Packet>}}
        """
        if packet.skippable: return
        
        # Store packet to drop packet which are receive twice
        timeout = time.time()+io.Packet.total_timeout
        self.__received_sema.acquire()
        self.__received[packet.id] = timeout 
        self.__received_sema.release()    

    def processPing(self, id):
        """ Process a new received ping.
        @type id: C{int}
        """
        self.__pinger.processPing(id)
        
    def processPong(self, id):
        """ Process a new received pong.
        @type id: C{int}
        """
        self.__pinger.processPong(id)
        
    def processAck(self, packet):
        """ Process new received acknoledge.
        @type packet: C{L{Packet<io.Packet>}}
        """
        # Read packet ID
        format  = "!I"
        if len(packet.data) != struct.calcsize(format): return None
        data = struct.unpack(format, packet.data)
        id = data[0]

        # Packet still exists ?
        self.__waitAck_sema.acquire()
        if not self.__waitAck.has_key(id):
            self.__waitAck_sema.release()
            return

        # Debug message
        if self.io.debug:
            t = time.time() - self.__waitAck[id].creation
            print "Ack %u received (time=%.1f ms)" % (id, t*1000)

        # The packet don't need ack anymore
        del self.__waitAck[id]
        self.__waitAck_sema.release()

    def disconnect(self):
        """ Disconnect client. """
        self.io.disconnectClient(self)

    def needAck(self, packet):
        """ Tell that a packet needs an acknoledge. """
        self.__waitAck_sema.acquire()
        self.__waitAck[packet.id] = packet
        self.__waitAck_sema.release()

    def live(self):
        """ Keep the connection alive :
        Resend packet if needed,
        clean old received packets,
        send ping if needed.
        """
        
        # Resend packet which don't have received their ack yet
        self.__waitAck_sema.acquire()
        waitAckCopy = self.__waitAck.copy()
        self.__waitAck_sema.release()
        for id,packet in waitAckCopy.items():
            if packet.timeout < time.time():
                if packet.sent < io.Packet.max_resend:
                    self.send(packet)
                else:
                    self.io.clientLostConnection(self)

        # Clean old received packets 
        self.__received_sema.acquire()
        receivedCopy = self.__received.copy()
        self.__received_sema.release()
        for id,timeout in receivedCopy.items():
            if timeout < time.time():
                if self.io.debug:
                    print "Supprime ancien paquet %u de %s:%u (timeout)" \
                        % (id, self.host, self.port)
                self.__received_sema.acquire()
                del self.__received[id]
                self.__received_sema.release()

        # Send ping if needed
        if self.send_ping: self.__pinger.live()

    def send(self, packet):
        """ Send packet to the client. """
        self.io.send(packet, to=self)
        
    def sendBinary(self, data):
        """ Send binary datas the client. """
        self.io.sendBinary(data, self)
