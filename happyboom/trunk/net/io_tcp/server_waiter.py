import socket
import thread
import traceback
from tcp_client import TCP_Client
from happyboom.common.log import log
from happyboom.common.thread import getBacktrace

class NetworkServerWaiter(object):
    def __init__(self, server):
        self.__server = server
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__port = None
        self.__host = ''
        self.__max_clients = None
        self.__nb_clients = 0
        self.__nb_clients_sema = thread.allocate_lock()
        self.__listening = False
        self.__listening_sema = thread.allocate_lock()
        self.__running = False

    def isRunning(self):
        return self.__running

    def runThread(self, port, max_connection):
        try:
            self.__running = True
            self.start(port, max_connection)
        except Exception, msg:
            log.error("EXCEPTION IN TCP SERVER WAITER!\n%s\n%s" \
                % (msg, getBacktrace()))
        self.__running = False 
        
    def clientConnect(self, client):
        if self.__server.debug:
            log.info("Client %s enter server %s." \
                % (client.name, self.__server.name))
        self.__nb_clients_sema.acquire()
        self.__nb_clients = self.__nb_clients + 1
        self.__nb_clients_sema.release()
        self.__server.clientConnect (client)

    def clientDisconnect(self, client):
        if self.__server.debug: log.info("New client : %s" % (client.getName()))
        self.__nb_clients_sema.acquire()
        self.__nb_clients = self.__nb_clients - 1
        self.__nb_clients_sema.release()

    def waitClient(self):
        try:
            (conn, addr) = self.__socket.accept()
        except socket.error, err:
            if err[0] == 11: # Resource temporarily unavailable
                return None
            raise
        if self.__max_clients <= self.getNbClients():
            if self.__server.debug:
                log.info( \
                    "Client %s refused on server %s (too many connection, %u/%u)." \
                    % (addr, self.__server.name, self.getNbClients(), self.__max_clients))
            conn.close()
            return None
        return TCP_Client(self.__server, addr, socket=conn)

    def start(self, port, max_connection):
        self.__max_clients = max_connection
        self.__port = port
        if self.__server.debug: 
            log.info("Start %s on port %u." \
                % (self.__server.name, port))
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.__socket.bind((self.__host, self.__port))
            self.__socket.listen(max_connection)
        except socket.error, err:
            if self.__server.debug:
                log.error("Binding error for %s." % (self.__server.name))
            if self.__server.on_binding_error != None:
                self.__server.on_binding_error (self.__server)
            return
        if self.__server.debug: 
            log.info("Server %s is listening (max=%u clients)." \
                % (self.__server.name, max_connection))
        self.__listening_sema.acquire()
        self.__listening = True 
        self.__listening_sema.release()

        while 1:
            try:
                client = self.waitClient()
                if client != None: self.clientConnect (client)
                client = None

            except socket.error, error:
                # Connection reset by peer.
                if error[0] == 104:
                    if client != None: client.disconnect()
                else:
                    raise

    def getNbClients(self):
        self.__nb_clients_sema.acquire()
        val = self.__nb_clients
        self.__nb_clients_sema.release()
        return val
    nb_clients = property(getNbClients)
    
    def getMaxClients(self):
        return self.__max_clients
    max_clients = property(getMaxClients)
        
    def getListening(self):
        self.__listening_sema.acquire()
        listening = self.__listening
        self.__listening_sema.release()
        return listening
    listening = property(getListening)

    def getPort(self):
        return self.__port
    port = property(getPort)
    
    def getHost(self):
        if self.__host == '': return 'localhost'
        return self.__host
    host = property(getHost)
