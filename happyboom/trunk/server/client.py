from happyboom.common.protocol import ProtocolException
from happyboom.common.log import log

class Client(object):
    """
    High-level class for a client in the server.
    """

    def __init__(self, io_client, gateway, client_manager):
        self.__io = io_client
        self.__client_manager = client_manager
        self.__gateway = gateway
        self.signature = None

    def __str__(self):
        return self.__io.__str__()

    def disconnect(self, reason):
        packet = self.__gateway.presentation.disconnectionPacket(reason)
        self.sendPacket(packet)
        self.stop()        

    # Stop client: close socket.
    def stop(self):
        self.__io.disconnect()

    # Read a message from network stack
    # Blocking function, returns None after timeout seconds (no data)
    def read(self, timeout):
        return self.__client_manager.readClientAnswer(self.__io, timeout)

    # Send a network packet the the client socket
    def sendPacket(self, packet):
        self.__io.send(packet)

    # Send a HappyBoom message to the client (see L{sendPacket})
    def sendNetMsg(self, func, event, *args):
        try:
            packet = self.__gateway.createMsg(func, event, *args)
        except ProtocolException, err:
            log.error(err)
            return
        self.__io.send(packet)

    def __getAddr(self): return self.__io.addr
    addr = property(__getAddr)
