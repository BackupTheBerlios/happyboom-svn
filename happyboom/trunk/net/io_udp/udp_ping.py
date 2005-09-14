import time
import struct
from net import io
from happyboom.common.log import log

class UDP_Ping:
    """ One UDP ping.
    @ivar timeout: Ping timeout (in seconds).
    @type timeout: C{float}
    @ivar creation: Creation time.
    @type creation: C{float}
    @ivar id: Ping id.
    @type id: C{int}
    """
    timeout = 5.000
    
    def __init__(self, id):
        """ Constuctor.
        @type id: C{int}
        """
        self.creation = time.time()
        self.timeout = self.creation+UDP_Ping.timeout
        self.id = id

    def getPacket(self):
        """ Create a network packet containing the ping. """
        ping = io.Packet()
        ping.type = io.Packet.PACKET_PING
        ping.writeStr( struct.pack("!I", self.id) )
        return ping    

class UDP_Pinger:
    """ An UDP pinger (send ping and process pong).
    @ivar ping_sleep: Sleep (in seconds) after sending one ping.
    @type ping_sleep: C{float}
    @ivar client: The UDP Client.
    @type client: C{L{UDP_Client<udp.UDP_Client>}}
    @ivar __sent_ping: List of sent pings (id,packet).
    @type __sent_ping: C{dict<int, L{UDP_Ping}>}
    @ivar __ping_id: Next ping id.
    @type __ping_id: C{int}
    @ivar __next_ping: Timer until next ping.
    @type __next_ping: C{float}
    """

    ping_sleep = 1.000
    
    def __init__(self, client):
        """ Constructor.
        @type client: C{L{UDP_Client<udp.UDP_Client>}}
        """
        self.__next_ping = time.time()+UDP_Pinger.ping_sleep
        self.__ping_id = 0
        self.client = client
        self.__sent_ping = {}

    def processPong(self, id):
        """ Process pong. """
        pass

    def sendPing(self):
        """ Send a new ping : create the packet and send it to the client. """
        self.__ping_id = self.__ping_id + 1
        ping = UDP_Ping(self.__ping_id)
        self.client.send( ping.getPacket() )
        self.__sent_ping[ping.id] = ping
                
    def pingTimeout(self, id):
        """ Function called when a ping timeout is raised.
        @parameter id: The ping id.
        @type id: C{int}
        """
        log.error("UDP ping timeout.")
#        log.error("Disconnect client %s:%u (ping timeout)." \
#            % (self.client.host, self.client.port))
#        self.client.disconnect()

    def live(self):
        """ Remove old ping and send ping if needed. """
        
        # Remove old ping
        for id,ping in self.__sent_ping.items():
            if ping.timeout < time.time():
                del self.__sent_ping[id]
                self.pingTimeout(id)
        
        # Send ping if needed
        if self.__next_ping < time.time():
            self.__next_ping = time.time()+UDP_Pinger.ping_sleep
            self.sendPing()

    def __getPingId(self, data):
        """ Utility used to get an ping id from binary data.
        @type data: C{str}
        """
        format  = "!I"
        if len(data) != struct.calcsize(format): return None
        data = struct.unpack(format, data)
        return data[0]

    def processPing(self, packet):
        """ Process ping : send pong.
        @type packet: C{L{Packet<io.Packet>}}
        """
        pong = io.Packet(skippable=True)
        pong.type = io.Packet.PACKET_PONG
        pong.writeStr( packet.data )
        self.client.send(pong)
        
    def processPong(self, packet):
        """ Process pong.
        @type packet: C{L{Packet<io.Packet>}}
        """
        id = self.__getPingId(packet.data)
        if id == None:
            if self.debug:
                log.warning("Received invalid udp ping packet!")
            return

        # Received too late ?
        if not self.__sent_ping.has_key(id): return

        # Remove ping from the list
        del self.__sent_ping[id]
