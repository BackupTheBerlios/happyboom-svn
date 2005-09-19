from happyboom.net.io.io_client import IO_Client
from happyboom.common.log import log
import socket

class TCP_Client(IO_Client):
    """ An TCP client.
    @ivar __socket: The TCP socket
    @type __socket: C{socket}
    @ivar on_send: Event called when a packet is sent to the client.
    @type on_send: C{function}
    @ivar on_receive: Event called when a new packet is received.
    @type on_receive: C{function}
    """
    def __init__(self, io_tcp, addr, name=None, socket=None):
        IO_Client.__init__(self, io_tcp, addr, name)
        self.__socket = socket 
        self.on_send = None
        self.on_receive = None

    def send(self, packet):
        """ Send a packet to the client.
        @type packet: Packet
        """
        self.sendBinary( packet.pack() )
    
    def sendBinary(self, data):
        """ Send binary datas to the client.
        @type data: str
        """
        if not self.connected: return
        try:
            self.__socket.send(data)
        except SocketError, err:
            # Broken pipe (32) or Connection reset by peer (104)
            if err[0] in (32, 104,):
                self.disconnect()
                return None
            raise

        # Call user event if needed
        if self.on_send != None: self.on_send(data)

    def receiveNonBlocking(self, max_size=1024):
        """ Non blocking read on the socket. """
        if not self.connected: return
        try:
            self.__socket.setblocking(0)
            data = self.__socket.recv(max_size)
        except socket.error, err:
            if err[0] == 11: return None
            # Broken pipe (32) or Connection reset by peer (104)
            if err[0] in (32, 104,):
                self.disconnect()
                return None
            raise
        return self.__processRecvData(data)

    def receiveBlocking(self, max_size=1024):
        """ Blocking read on the socket. """
        if not self.connected: return
        try:
            self.__socket.setblocking(1)
            data = self.__socket.recv(max_size)
        except socket.error, err:
            # Broken pipe (32) or Connection reset by peer (104)
            if err[0] in (32, 104,):
                self.disconnect()
                return None
            raise
        return self.__processRecvData(data)

    def disconnect(self):
        """ Disconned the client : close the socket. """
        self.__socket.close()
        IO_Client.disconnect(self)

    def __processRecvData(self, data):
        # If no data, connection is lost
        if len(data)==0:
            if self.io.verbose:
                log.warning("Client %s lost connection with server!" % self)
            self.disconnect()
            return None

        # Call user event if needed
        if self.on_receive != None: self.on_receive(data)
        return data
