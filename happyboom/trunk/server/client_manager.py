from happyboom.net import io, io_udp, io_tcp, net_buffer
import thread, traceback, time

class ClientManager(object):
    def __init__(self, arg): 
        self.__server = None 
        self.__io = io_tcp.IO_TCP(is_server=True)
        self.__io.debug = arg.get("debug", False)
        self.__io.verbose = arg.get("verbose", False)
        self.__buffer = net_buffer.NetBuffer()
        self.__debug = arg.get("debug", False)
        self.__verbose = arg.get("verbose", False)
        self.max_clients = arg.get("max_clients", 2)
        self.client_port = arg.get("client_port", 12430)
        self.__supported_features = {}
        self.__clients = []
        self.__clients_sema = thread.allocate_lock()
        
    def recvClientPacket(self, packet):
        self.__buffer.append(packet.recv_from.addr, packet)

    def stop(self):
        for client in self.__clients:
            client.stop()

    def process(self):
        pass
#        processInputs()

    def start(self):
        if self.__verbose: print "[*] Starting server"
        self.__io.name = "server"
        self.__io.on_client_connect = self.openClient
        self.__io.on_client_disconnect = self.closeClient
        self.__io.on_new_packet = self.recvClientPacket
        self.__io.connect('', self.client_port)
        thread.start_new_thread(self.run_io_thread, ())

    def readClientAnswer(self, client, timeout=1.000):
        answer = self.__buffer.readBlocking(client.addr, timeout)
        if answer==None: return None
        return answer.data

    def registerFeature(self, client, role):
        if role in self.__supported_features:
            if client not in self.__supported_features[role]:
                self.__supported_features[role].append(client)
        else:
            self.__supported_features[role] = [client,]
        
    def openClient(self, client):
        # TODO: Ne pas utiliser de thread ?!
        thread.start_new_thread( self.__clientChallenge, (client,self.__do_openClient))

    def closeClient(self, client):
        if self.__verbose:
            log.info("Client %s disconnected." % client.name)
        
        txt = "Client %s (display) leave us." % (client.name)
        self.__gateway.sendText(txt)
        
        client.sendMsg("presentation", "bye", "utf8", u"Lost connection")
        
    def __clientChallenge(self, client, func):
        try:
            func(client)
        except Exception, msg:
            print "EXCEPTION WHEN A CLIENT TRY TO CONNECT :"
            print msg
            print "--"
            traceback.print_exc()
            self.stop()

    # Function which should be called in a thread
    # TODO: Pourquoi c'est utilisé ça ?
    def run_io_thread(self):
        try:
            while self.__io.isRunning():
                self.__io.live()                
                time.sleep(0.001)
        except Exception, msg:
            print "EXCEPTION IN IO THREAD :"
            print msg
            print "--"            
            traceback.print_exc()
            self.stop()

    def generateSignature(self, client):
        import random
        r = random.randint(0,1000000)
        return r

    def __do_openClient(self, io_client):
        if self.__verbose: print "[*] Display %s try to connect ..." % (client.name)
        client = ClientSocket(io_client, self)
        
#        self.__buffer.clear(client.addr)
       
        # Check protocol version (max: wait 200ms)
        answer = self.readClientAnswer(client, 0.200)
        if answer != self.__gateway.protocol_version:
            # If it isn't the right version, send presention.bye(...)
            txt = u"Sorry, you don't have same protocol version (%s VS %s)" \
                % (answer, self.__gateway.protocol_version)
            client.sendMsg("presentation", "bye", "utf8", txt)

            # Wait 0.5s and then disconnect the client
            time.sleep(0.500)
            client.disconnect()
            return
            
        # Send protocol version with "hello()"
        client.signature = self.generateSignature()        
        client.send("presentation", "hello", \
            "bin", self.__gateway.protocol_version, \
            "bin", signature)
         
        # Read features (max: wait 1sec)
        answer = client.read(1.0)
        #TODO: do something with answer :-)

        self.__clients_sema.acquire() 
        self.__clients.append(client)
        self.__clients_sema.release() 

        txt = "Welcome to new (display) client : %s" % (client.name)
        self.__gateway.sendText(txt)
        if self.__verbose: print "[*] Display %s connected" % (client.name)
        self.sendBBMessage("sync")

    def __getSupportedFeatures(self): return self.__supported_features
    supported_features = property(__getSupportedFeatures)


