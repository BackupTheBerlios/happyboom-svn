from happyboom.net.io_tcp.tcp import IO_TCP
from happyboom.common.packer import unpackBin
from happyboom.common.log import log
from happyboom.common.thread import getBacktrace
from happyboom.server.client import Client
from happyboom.common.event import EventLauncher
import thread, time

class ClientManager(EventLauncher, object):
    def __init__(self, protocol, arg): 
        EventLauncher.__init__(self)
        self.server = None 
        self.__protocol = protocol
        self.__io = IO_TCP(is_server=True)
        self.__io.debug = arg.get("debug", False)
        self.__io.verbose = arg.get("verbose", False)
        self.__debug = arg.get("debug", False)
        self.__verbose = arg.get("verbose", False)
        self.max_clients = arg.get("max_clients", 2)
        self.client_port = arg.get("client_port", 12430)
        self.__supported_features = {}
        self.__clients = {}
        self.__clients_lock = thread.allocate_lock()
        self.gateway = None
        self.presentation = None

    def onClientDisconnection(self, ioclient, reason):
        log.info("Client %s leave us: %s" % (ioclient, reason))
        self.closeClient(ioclient)

    def onClientConnection(self, ioclient, version, signature):
        # TODO: Case where signature != "" ??? (reconnection)
        if self.__verbose: log.info("Client %s try to connect : check version." % ioclient)
        server_version = self.__protocol.version
        if version == server_version:
            if self.__verbose: log.info("Client %s try to connect: version ok." % ioclient)
            signature = self.generateSignature(ioclient)
            self.launchEvent("happyboom", "connection", ioclient, server_version, signature)
        else:    
            if self.__verbose: log.warning("Client %s try to connect: wrong version (%s)." % version)
            self.launchEvent("happyboom", "closeConnection", ioclient, u"Wrong server version (%s VS %s)" % (version, serveur_version))

    def onClientFeatures(self, ioclient, features):
        # Register client in the clients list
        client = Client(ioclient, self.gateway, self)
        self.__clients_lock.acquire() 
        self.__clients[client.addr] = client
        self.__clients_lock.release() 

        # Register client to features
        for feature in features:
            f = self.__protocol.getFeatureById(ord(feature))
            feature = f.name
            if self.__verbose: log.info("Register feature %s for client %s" % (feature, client))
            if feature in self.__supported_features:
                self.__supported_features[feature].append(ioclient)
            else:
                self.__supported_features[feature] = [ioclient]
            client.features.append(feature)
      
        # Send message to network and to the log
        txt = u"Welcome to new (display) client : %s" % client
        log.info("[*] Client %s connected" % client)
        self.launchEvent("happyboom", "network", "info", "notice", txt)
        self.launchEvent("happyboom", "newClient", client)

    def stop(self):
        for client in self.__clients.values():
            client.stop()

    def process(self):
        if not self.__io.isRunning():
            self.server.stop()

    def start(self):
        if self.__verbose: log.info("[*] Starting server")
        self.__io.name = "server"
        self.__io.on_client_connect = self.openClient
        self.__io.on_client_disconnect = self.closeClient
        self.__io.on_new_packet = self.presentation.processPacket
        self.__io.connect('', self.client_port)
        self.launchEvent("happyboom", "register", "connection", self.onClientConnection)
        self.launchEvent("happyboom", "register", "disconnection", self.onClientDisconnection)
        self.launchEvent("happyboom", "register", "features", self.onClientFeatures)
        thread.start_new_thread(self.run_io_thread, ())

    def registerFeature(self, client, role):
        if role in self.__supported_features:
            if client not in self.__supported_features[role]:
                self.__supported_features[role].append(client)
        else:
            self.__supported_features[role] = [client,]
        
    def openClient(self, ioclient):
        if self.__verbose: log.info("[*] Client %s try to connect ..." % ioclient)

    def removeClient(self, ioclient):
        if self.__verbose: log.info("Disconnect client %s." % ioclient)
        self.gateway.sendText(u"Client %s leave us." % ioclient)

        self.__clients_lock.acquire() 
        del self.__clients[ioclient.addr]
        self.__clients_lock.release() 
    
    def closeClient(self, ioclient):
        # TODO: get client of type Client for the client of type ClientIO to send
        # him bye
#        client.sendNetMsg("presentation", "bye", "utf8", u"Lost connection")
        client = self.getClientByAddr(ioclient.addr)
        if client == None: return
        log.info("[*] Client %s leave us." % client)
        self.removeClient(ioclient)
        
    def __clientChallenge(self, client, func):
        try:
            func(client)
        except Exception, msg:
            log.error( \
                "EXCEPTION WHEN A CLIENT TRY TO CONNECT :\n%s\n%s" \
                % (msg, getBacktrace()))
            self.stop()

    # Function which should be called in a thread
    # TODO: Why is this used?
    def run_io_thread(self):
        try:
            while self.__io.isRunning():
                self.__io.live()                
                time.sleep(0.001)
        except Exception, msg:
            log.error( \
                "EXCEPTION IN IO THREAD :\n%s\n%s" \
                % (msg, getBacktrace()))
            self.server.stop()

    def generateSignature(self, ioclient):
        import random
        r1 = random.randint(0,1000000)
        r2 = random.randint(0,1000000)
        return "%s%s%s" % (r1,ioclient.addr,r2)

    def getClientByAddr(self, addr):
        """ Returns None if no client matchs. """
        self.__clients_lock.acquire() 
        client = self.__clients.get(addr, None)
        self.__clients_lock.release() 
        return client
        
    def __getSupportedFeatures(self): return self.__supported_features
    supported_features = property(__getSupportedFeatures)


