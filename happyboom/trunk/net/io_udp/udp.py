# -*- coding: ISO-8859-1 -*-

import time
import thread
import socket
import traceback
import struct
from net.io.base_io import BaseIO
from net.io.packet import Packet
from udp_client import UDP_Client
from happyboom.common.log import log
from happyboom.common.thread import getBacktrace

class IO_UDP(BaseIO):
    """ IO for UDP transport.
    @ivar packet_timeout: Try to send a packet until this timeout.
    @type packet_timeout: C{float}
    @ivar thread_sleep: Sleep time used in the thread.
    @type thread_sleep: C{float}
    @ivar __is_server: ??? 
    @type __is_server: C{bool}
    @ivar __server: The server (only used by clients, None else).
    @type __server: ?
    @ivar __running: Is the thread running ?
    @type __running: C{bool}
    @ivar __socket: The network socket.
    @type __socket: C{socket}
    @ivar __socket_open: Is the network socket L{__socket} opened ?
    @type __socket_open: C{bool}
    @ivar __addr: The IO network address (host, port).
    @type __addr: C{(string, string,)}
    @ivar __packet_id: ???
    @type __packet_id: C{int}
    @ivar __clients: List of clients connected to this IO.
    @type __clients: C{list<L{IO_client<io.IO_Client>}>?}
    @ivar __clients_sema: Lock used to access L{__clients}.
    @type __clients_sema: C{thread.lock}
    """
    
    def __init__(self, is_server=False):
        """ Constructor. """
        BaseIO.__init__(self)
        self.packet_timeout = 1.000
        self.thread_sleep = 0.010

        self.__is_server = is_server
        self.__server = None # only used in client mode
        self.__running = True

        self.__socket = None
        self.__socket_open = False        
        self.__addr = None
        self.__packet_id = 0
        self.__clients = {}
        self.__clients_sema = thread.allocate_lock()

    def connect(self, host, port):
        """ Connect to host:port 
        @type host: C{str}
        @type port: C{int}
        """
        if host != "":
            host = socket.gethostbyname(host)
        else:
            host = "127.0.0.1"
        self.__addr = (host, port,)
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.__is_server:
            if self.verbose:
                log.info("Run server on port %u (udp)." % self.port)
            self.__socket.bind(("",port,))
        else:
            if self.verbose:
                log.info("Connect to server %s:%u." % (self.host, self.port))
            self.__server = UDP_Client(self, self.__addr)
            self.__server.name = "server"
            self.__server.send_ping = True
            self.__clients_sema.acquire()
            self.__clients[self.__addr] = self.__server
            self.__clients_sema.release()

        self.__socket_open = True
        self.__socket.setblocking(0)

        if not self.__is_server:
            self.send( Packet("I'm here") )
        
        BaseIO.connect(self, host, port)

        # Call user event if needed
        if self.on_connect != None: self.on_connect()

    def disconnect(self):
        """ Close connection. """
        if not self.__socket_open: return
        self.__socket.close()
        self.__socket_open = False
        if self.on_disconnect != None: self.on_disconnect()
        self.stop()

    def disconnectClient(self, client):
        """ Disconnect a client.
        @type client: C{L{IO_Client<io.IO_Client>}}
        """
        self.__clients_sema.acquire()
        if self.__clients.has_key(client.addr): del self.__clients[client.addr]
        self.__clients_sema.release()
        if self.verbose:
            log.info("Disconnect client %s." % client)
        if self.on_client_disconnect != None: self.on_client_disconnect(client)
    
    def send(self, packet, to=None):
        """ Send a packet to the server or to all clients.
        @type packet: C{L{Packet<io.Packet>}}
        @type to: C{L{IO_Client<io.IO_Client>}}
        """
        if not self.__socket_open: return
        first_send = (packet.sent == 0)
        
        # No client, exit !
        if self.__is_server:
            self.__clients_sema.acquire()
            nb_clients = len(self.__clients)
            self.__clients_sema.release()
            if nb_clients==0: return None

        # Prepare the packet
        packet.prepareSend()
        if first_send:
            # First send : give an ID to the packet
            self.__packet_id = self.__packet_id + 1
            packet.id = self.__packet_id
            if self.debug: packet.creation = time.time()
        need_ack = first_send and not packet.skippable
        
        # Read binary version of the packet
        data = packet.pack()

        # Send data to client(s)
        if self.__is_server:
            if to==None:
                for addr,client in self.clients.items(): # use internal copy for clients
                    self.__sendDataTo(packet, data, client, need_ack)
            else:
                self.__sendDataTo(packet, data, to, need_ack)
        else:
            self.__sendDataTo(packet, data, self.__server, need_ack)
        
    def sendBinary(self, data, client):
        """ Send binary data that doesn't need an acknoledge. 
        @type data: C{str}
        @type client: C{L{IO_Client<io.IO_Client>}}
        """        
        if self.debug:
            log.info("Send data %s to %s (without ack)" % (data, client))
        self.__socket.sendto(data, client.addr)    
        
        # Call user event if needed
        if self.on_send != None: self.on_send(data)
    
    def __sendDataTo(self, packet, data, client, need_ack):
        """ Send binary data with an acknoledge to a client.
        @type data: C{str}
        @type client: C{L{IO_Client<io.IO_Client>}}
        @type need_ack: C{bool}
        """
        if self.debug:
            log.info("Send packet %s to %s" % (packet.toStr(), client))
        self.__socket.sendto(data, client.addr)

        # If the packet need an ack, add it to the list
        if need_ack: client.needAck(packet)
        
        # Call user event if needed
        if self.on_send != None: self.on_send(data)
    
    def receive(self, max_size = 1024):
        """ Read a packet from the socket.
        Returns None if there is not new data.
        @type max_size: C{int}
        @rtype: C{L{Packet<io.Packet>}}
        """
        if not self.__socket_open: return None

        # Try to read data from the socket
        try:                        
            data,addr = self.__socket.recvfrom(max_size)
        except socket.error, err:
            if err[0] == 11: return None
            raise
    
        # New client ?
        return self.__processRecvData(data, addr)

    def live(self):                
        """ Keep the connection alive. """
        # Resend packets which don't have received their ack
        for addr, client in self.clients.items(): # use internal copy for clients
            client.live()                            
                    
        # Read data from network (if needed)
        packet = self.receive()                
        if packet != None: self.__processNewPacket(packet)
                    

    def clientLostConnection(self, client):
        if self.__is_server:
            self.__lostClient(client)
        else:
            self.lostConnection()

    def __lostClient(self, client):
        if not client.addr in self.__clients: return
        client = self.__clients[client.addr]
        if self.verbose:
            log.warning("Lost connection with client %s !" % client)
        self.disconnectClient(client)
    
    def lostConnection(self):
        if self.verbose:
            log.warning("Lost connection to %s:%u!" % (self.host, self.port))
        if self.__socket_open:
            self.__socket.close()
            self.__socket_open = False
        if self.on_lost_connection: self.on_lost_connection()
        self.stop()
    
    def run_thread(self):
        """ Function which should be called in a thread : call L{live()} with a sleep. """
        try:
            while self.__running:
                self.live()                
                time.sleep(self.thread_sleep)
        except Exception, msg:
            log.error( \
                "EXCEPTION IN UDP SERVER:\n%s\n%s" \
                % (msg, getBacktrace()))
            self.stop()

    def stop(self):
        if not self.__running: return
        self.__running = False 
        self.disconnect()

    def isRunning(self): return self.__running

    #--- Private functions ------------------------------------------------------

    def __processRecvData(self, data, addr):
        if self.__is_server:
            self.__clients_sema.acquire()
            if addr not in self.__clients:
                client = UDP_Client(self, addr)
                self.__clients[addr] = client
                self.__clients_sema.release()
                if self.verbose: log.info("New client: %s:%u." % (addr[0], addr[1]))
                client.send_ping = True
                if self.on_client_connect != None: self.on_client_connect(client)
            else:
                client = self.__clients[addr] 
                self.__clients_sema.release()
        else:
            # Drop packets which doesn't come from server
            if self.__server.addr != addr:
                if self.debug:
                    log.warning("Drop packet from %s:%u (it isn't the server address)." % (addr[0], addr[1]))
                return None
            client = self.__server
    
        # Call user event if needed
        if self.on_receive != None: self.on_receive(data)
                    
        # Decode data to normal packet (unpack) 
        packet = Packet()
        packet.unpack(data)
        if not packet.isValid():
            if self.debug:
                log.warning("Drop invalid network packet from %s" % (data, client))
            return None
        
        # Return packet
        packet.recv_from = client 
        return self.__processPacket(packet)

    def __processPacket(self, packet):
        client = packet.recv_from

        if self.debug:
            log.info("Received packet %s from %s:%u" % (packet.toStr(), client.host, client.port))
        
        # Send an ack if needed
        if not packet.skippable: self.__sendAck(packet)
        
        # Is is a special packet (ack / ping / poing) ?
        if packet.type == Packet.PACKET_ACK:
            client.processAck(packet)
            return None
        if packet.type == Packet.PACKET_PING:
            client.processPing(packet)
            return None
        if packet.type == Packet.PACKET_PONG:
            client.processPong(packet)
            return None
            
        # This packet is already received ? Drop it!
        if client.alreadyReceived(packet.id):
            if self.debug:
                log.warning("Drop packet %u (already received)" % packet.id)
            return None    
            
        client.receivePacket(packet)
        
        # Returns the new packet
        return packet

    def __sendAck(self, packet):
        """ Send an ack for a packet.
        @type packet: C{L{Packet}}
        """
        # Write ack to socket
        data = struct.pack("!I", packet.id)
        ack = Packet(data)
        ack.type = Packet.PACKET_ACK
        ack.skippable = True        
        packet.recv_from.send(ack)

    def __processNewPacket(self, packet):
        """ Do something with a new packet
        @type packet: C{L{Packet}}
        """
        if self.verbose:
            log.info("New udp message : %s" % packet.toStr())
        if self.on_new_packet != None: self.on_new_packet(packet)        

    def __getPort(self):
        return self.__addr[1]

    def __getHost(self):
        if self.__addr[0]=='': return "localhost"
        return self.__addr[0]

    def __getAddr(self): return self.__addr

    def _getName(self):
        if self._name != None: return self._name
        return self.host
        
    def __getClients(self):
        self.__clients_sema.acquire()
        clients = self.__clients.copy()
        self.__clients_sema.release()
        return clients

    def __getMaxClients(self):
        return 0
        
    #--- Properties -------------------------------------------------------------

    name = property(_getName, BaseIO._setName, doc="The IO name")
    addr = property(__getAddr, doc="The IO addresse (host, port).")
    port = property(__getPort, doc="The network port number.")
    host = property(__getHost, doc="The network hostname.")
    clients = property(__getClients, doc="List of clients.")
    max_clients = property(__getMaxClients, doc="Maximum number of clients connected to the server.")
