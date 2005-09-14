class Client:
    """
    High-level class for a client in the server.
    """

    def __init__(self, io_client, client_manager):
        self.__io = io_client
        self.__client_manager = client_manager
        self.signature = None

    # Stop client: close socket.
    def stop(self):
        self.__io.stop()

    # Read a message from network stack
    # Blocking function, returns None after timeout seconds (no data)
    def read(self, timeout):
        return self.__client_manager.readClientAnswer(self.__io, timeout)

    # Send a network packet the the client socket
    def sendPacket(self, packet):
        self.__io.send(packet)

    # Send a HappyBoom message to the client (see L{sendPacket})
    def sendNetMsg(self, func, event, *args):
        packet = self.__gateway.createMsgTuple(func, event, args)
        self.__io.send(packet)
