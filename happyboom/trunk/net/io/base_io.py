#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-

import time
import threading
import socket
import traceback
import struct
from packet import Packet
from io_client import IO_Client

class BaseIO(object):
    """
    Base IO virtual class.

    @ivar verbose: Is verbose ?
    @type verbose: C{bool}
    @ivar debug: Display debug messages ?
    @type debug: C{bool}
    @ivar on_connect: Event called when the IO try to connect.
    @type on_connect: C{function()}
    @ivar on_connection_fails: Event called when the IO fails to connect to server.
    @type on_connection_fails: C{function()}
    @ivar on_disconnect: Event called when the server try to disconnect.
    @type on_disconnect: C{function()}
    @ivar on_client_connect: Event called when a new client try to connect to the server.
    @type on_client_connect: C{function(L{IO_Client})}
    @ivar on_client_disconnect: Event called when a client is disconnected.
    @type on_client_disconnect: C{function(L{IO_Client})}
    @ivar on_new_packet: Event called when a new packet is received.
    @type on_new_packet: C{function(L{Packet})}
    @ivar __name: The IO name.
    @type __name: C{str}
    """
    
    def __init__(self, is_server=False):
        """
        Constructor.
        @type is_server: C{bool}
        """
        self.debug = False
        self.verbose = False 
        self._is_ready = False

        # Events
        self.on_connect = None            # No argument
        self.on_connection_fails = None   # No argument
        self.on_lost_connection = None    # No argument
        self.on_disconnect = None         # No argument
        self.on_client_connect = None     # (client)
        self.on_client_disconnect = None  # (client)
        self.on_new_packet = None         # (packet) : client address
        self.on_send = None               # (data)
        self.on_receive = None            # (data)

        self.__name = None

    def connect(self, host, port):
        """ Connect to host:port.
        @parameter host: Network hostname.
        @type host: C{str}
        @parameter port: Network port number.
        @type port: C{int}
        """
        if self.__name==None:
            self.__name = "%s:%u" % (host, port)

    def disconnect(self):
        """ Close connection. """
        pass

    def send(self, packet, to=None):
        """ Send a packet to the server or to all clients. """
        pass
    
    def receive(self, max_size = 1024):
        """ Read a packet from the socket. Returns None if there is not new data.
        @parameter max_size: Maximum packet size (in bytes).
        @type max_size: C{int}
        @rtype: C{L{Packet}}
        """
        pass

    def live(self):                
        """ Keep the connection alive. """
        pass

    def disconnectClient(self, client):
        """ Disconnect an IO client.
        @type client: L{IO_Client}
        """
        pass
    
    def run_thread(self):
        """ Run the IO thread (will call L{live()} itself). """
        pass
    
    def stop(self):
        """ Stop the IO (close connections). """
        pass

    def __str__(self):
        return self.__name

    #--- Private functions ------------------------------------------------------

    def __getName(self):
        if self.__name == None: return "no name"
        return self.__name
    
    def __setName(self, name):
        self.__name = name

    def __getReady(self):
        return self._is_ready

    #--- Properties -------------------------------------------------------------

    name = property(__getName, __setName, doc="The IO name.")
    is_ready = property(__getReady, doc="Tells if the IO is ready to use.");
