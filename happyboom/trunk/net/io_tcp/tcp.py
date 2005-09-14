#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

import time
import thread
import socket
import traceback
import struct
from tcp_client import TCP_Client
from happyboom.net.io.packet import Packet
from happyboom.net.io.base_io import BaseIO
from server_waiter import NetworkServerWaiter
from happyboom.common.log import log
from happyboom.common.thread import getBacktrace

class IO_TCP(BaseIO):
    """
    IO for TCP transport.
    @ivar packet_timeout: Timeout of packets (in seconds)
    @type packet_timeout: C{float}
    @ivar thread_sleep: Sleep time used in the thread (in seconds).
    @type thread_sleep: C{float}
    @ivar __is_server: ??? 
    @type __is_server: C{bool}
    @ivar __waiter: Class which wait for clients.
    @type __waiter: NetworkServerWaiter
    @ivar __addr: The IO network address (host, port).
    @type __addr: C{(string, string,)}
    @ivar __clients: List of clients connected to this IO.
    @type __clients: C{list<L{IO_client<io.IO_Client>}>?}
    @ivar __clients_sema: Semaphore used to access L{__clients}.
    @type __clients_sema: C{thread.lock}
    """
    
    def __init__(self, is_server=False):
        BaseIO.__init__(self)
        self.packet_timeout = 1.000
        self.thread_sleep = 0.010

        self.__is_server = is_server

        self.__waiter = NetworkServerWaiter(self)
        self.__addr = None
        self.__clients = {}
        self.__server = None
        self.__clients_sema = thread.allocate_lock()
        Packet.use_tcp = True

    def connect(self, host, port):
        """ Connect to host:port """
        max_connection = 50
    
        self.__addr = (host, port,)
        if self.__is_server:
            if self.verbose:
                log.info("Run server at %s:%u (tcp)" % (self.host, self.port))
            thread.start_new_thread( self.__waiter.run_thread, (port,max_connection,))
        else:
            if self.verbose:
                log.info("Connect to server %s:%u" % (self.host, self.port))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect(self.__addr)
            except socket.error, err:
                if err[0]==111:
                    if self.verbose:
                        log.warning("Fail to connect to server %s:%u" % (self.host, self.port))
                    if self.on_connection_fails:
                        self.on_connection_fails()
                    return
                raise

            client = TCP_Client(self, self.__addr, socket=s)
            self.__server = client
            self.__clients_sema.acquire()
            self.__clients[client.addr] = client
            self.__clients_sema.release()

        if self.on_connect != None: self.on_connect()
        BaseIO.connect(self, host, port)
        self._is_ready = True

    def disconnect(self):
        """ Close connection """
        self.__clients_sema.acquire()
        clients = self.__clients.copy()
        self.__clients_sema.release()
        for client_addr, client in clients.items():
            client.disconnect()
        if self.on_disconnect != None: self.on_disconnect()
        self.stop()

    def disconnectClient(self, client):
        """ Disconnect a client. """
        self.__clients_sema.acquire()
        if  self.__clients.has_key(client.addr): del self.__clients[client.addr]
        self.__clients_sema.release()
        if self.verbose:
            log.info("Disconnect client %s." % client)
        if self.on_client_disconnect != None: self.on_client_disconnect (client)
        if self.__server == client: self.disconnect()
    
    def send(self, packet, to=None):
        """ Send a packet to the server or to all clients
        @type packet: Packet
        """
        if not self._running: return
        
        # Read binary version of the packet
        data = packet.pack()

        if self.__is_server:
            if to==None:
                self.__clients_sema.acquire()
                clients = self.__clients.copy()
                self.__clients_sema.release()    
                for client in clients:
                    client.sendBinary(data)
            else:
                to.sendBinary(data)
        else:
            self.__server.sendBinary(data)

    def live(self):                
        """ Keep the connection alive :
        - Get clients new packets
        - Process packets (eg. ping/pong)
        """
        clients = self.clients
        for client_addr, client in clients.items():
            data = client.receiveNonBlocking()
            if data != None:
                self.__processData(client, data)

    def __processData(self, client, data):
        while data != "":
            packet = Packet()
            packet.recv_from = client
            data = packet.unpack(data)
            if not packet.isValid():
                if self.debug:
                    log.warning("Received buggy network packet from %s!" % client)
                return
            if self.debug:
                log.info("Received %s:%u => \"%s\"" % (client.host, client.port, packet.data))
            if self.on_new_packet: self.on_new_packet(packet)
    
    def run_thread(self):
        """ Function which should be called in a thread. """
        try:
            while self._running:
                self.live()                
                time.sleep(self.thread_sleep)
        except Exception, msg:
            log.error( \
                "EXCEPTION DANS LE THREAD IO :\n%s\n%s"
                % (msg, getBacktrace()))
        self.stop()

    #--- Private functions ------------------------------------------------------

    def __getPort(self):
        return self.__addr[1]

    def __getHost(self):
        if self.__addr[0]=='': return "localhost"
        return self.__addr[0]

    def __getAddr(self): return self.__addr

    def __getName(self):
        if self.__name != None: return self.__name
        return self.host
        
    def __setName(self, name):
        self.__name = name    

    def __getClients(self):
        self.__clients_sema.acquire()
        clients = self.__clients.copy()
        self.__clients_sema.release()
        return clients

    def __getMaxClients(self):
        return 0
    
    def clientConnect(self, client):
        client.on_receive = self.on_receive
        client.on_send = self.on_send
        self.__clients_sema.acquire()
        self.__clients[client.addr] = client
        self.__clients_sema.release()
        if self.on_client_connect != None: self.on_client_connect (client)
        
    def clientDisconnect(self, client):
        if self.verbose:
            log.info("Client %s leave server %s." % (client, self))
        self.__clients_sema.acquire()
        self.__clients.remove(client)
        self.__clients_sema.release()
        self.__waiter.client_disconnect(client)
        if self.on_client_disconnect != None: self.on_client_disconnect (client)
        
    #--- Properties -------------------------------------------------------------

    name = property(__getName, __setName)
    addr = property(__getAddr)
    port = property(__getPort)
    host = property(__getHost)
    clients = property(__getClients)
    max_clients = property(__getMaxClients)
