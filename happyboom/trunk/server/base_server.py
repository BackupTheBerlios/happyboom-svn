# TODO: Check if it's always possible to send skippable packets

from happyboom.common.packer import HappyBoomPacker
from happyboom.net import io, io_udp, io_tcp, net_buffer
from pysma import Kernel, DummyScheduler, ActionAgent, ActionMessage
import re, random, thread, traceback, time
import types # maybe only used for assertions

class HappyBoomClient:
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

class HappyBoomAgent(ActionAgent):
    """
    SMA agent in HappyBoom.
    """
    def __init__(self, type, **args):
        ActionAgent.__init__(self, prefix="msg_")
        self.type = type
        self.__debug = args.get("debug", False)

    def born(self):
        self.requestRole(self.type)

    def requestActions(self, type):
        self.requestRole("%s_listener" %type)
        
    def sendBBMessage(self, action, *arg, **kw):
        message = BoomBoomMessage("%s_%s" %(self.type, action), arg, kw)
        self.sendBroadcastMessage(message, "%s_listener" %self.type)

    def messageReceived(self, msg):
        if self.__debug:
            print "Unhandled message : %s -- %s" %(type(self), msg)

class HappyBoomMessage(ActionMessage):
    def __init__(self, action, arg, kw={}):
        ActionMessage.__init__(self, action, arg, kw)

# TODO: Use better name :-)
class HappyBoomPackerException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

class HappyBoomGateway(HappyBoomAgent):
    def __init__(self, server, arg):
        self.__server = server
        HappyBoomAgent.__init__(self, "gateway")
        self.nextChar = None
        self._debug = arg.get("debug", False)
        self._verbose = arg.get("verbose", False)
        Kernel().addAgent(DummyScheduler(sleep=0.01))
        self.packer = HappyBoomPacker()

    # Create a network packet for the event func.event(args) where
    # args is a tuple
    def createMsgTuple(self, func, event, args):
        data = self.packer.pack(func, event, args)
        return io.Packet(data)
            
    # Create a network packet for the event func.event(args), see
    # L{self.createMsgTuple}
    def createMsg(self, func, event, *args):
        return self.createMsgTuple(func, event, args)

    def start(self):
        Kernel.instance.addAgent(self)
        
    def stop(self):
        Kernel.instance.stopKernel()

    def sendText(self, txt, client=None):
        if client != None:
            client.sendMsg("agent_manager", "Text", txt)
        else:
            self.sendNetMsg("agent_manager", "Text", txt)

    def sendMsg(self, func, event, *args):
        packet = self.createMsgTuple(role, type, args, func)
        clients = self.__server.client_manager.supported_features.get(role, ())
        for client in clients:
            client.sendPacket(packet)

class HappyBoomClientManager(object):
    def __init__(self, server, gateway, arg): 
        self.__server = server
        self.__gateway = gateway
        self.__io = io_tcp.IO_TCP(is_server=True)
        self.__io.debug = arg.get("debug", False)
        self.__io.verbose = arg.get("verbose", False)
        self.__buffer = net_buffer.NetBuffer()
        self.__debug = arg.get("debug", False)
        self.__verbose = arg.get("verbose", False)
        self.max_clients = arg.get("max_clients", 2)
        self.client_port = arg.get("client_port", 12430)
        self.__protocol_version = "0.1.4"
        self.__supported_features = {}
        self.__clients = []
        self.__clients_sema = thread.allocate_lock()
        
    def recvClientPacket(self, packet):
        self.__buffer.append(packet.recv_from.addr, packet)

    def stop(self):
        self.__gateway.sendNetMsg("game", "stop")
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
        client = HappyBoomClientSocket(io_client, self)
        
#        self.__buffer.clear(client.addr)
       
        # Check protocol version (max: wait 200ms)
        answer = self.readClientAnswer(client, 0.200)
        if answer != self.__protocol_version:
            # If it isn't the right version, send presention.bye(...)
            txt = u"Sorry, you don't have same protocol version (%s VS %s)" \
                % (answer, self.__protocol_version)
            client.sendMsg("presentation", "bye", "utf8", txt)

            # Wait 0.5s and then disconnect the client
            time.sleep(0.500)
            client.disconnect()
            return
            
        # Send protocol version with "hello()"
        client.signature = self.generateSignature()        
        client.send("presentation", "hello", \
            "bin", self.__protocol_version, \
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

class HappyBoomServer(object):
    def __init__(self, arg): #verbose=False, debug=False):
        self.started = False
        self.__debug = arg.get('debug', False)
        self.__verbose = arg.get('verbose', False)
        self.__stopped = False
        self.__stoplock = thread.allocate_lock()
        if arg.has_key("gateway"):
            self.__gateway = arg["gateway"]
        else:
            self.__gateway = HappyBoomGateway(self, arg)
        self.__client_manager = HappyBoomClientManager(self, self.__gateway, arg)
        random.seed()
        self.__items = []
        
    def born(self):
        self.gateway.born()
        
    def start(self):
        if self.__verbose: print "[*] Starting server..."
        self.__client_manager.start()
        self.__gateway.start()
        print "[*] Server started"
        
        self.__stoplock.acquire()
        running = not self.__stopped
        self.__stoplock.release()
        while running:
            self.__client_manager.process()
            time.sleep(0.01)
            self.__stoplock.acquire()
            running = not self.__stopped
            self.__stoplock.release()

    def stop(self):
        self.__stoplock.acquire()
        if self.__stopped:
            self.__stoplock.release()
            return
        self.__stopped = True
        self.__stoplock.release()
        print "[*] Stopping server..."
        self.__gateway.stop()
        self.__client_manager.stop()
        if self.__verbose: print "[*] Server stopped"

    def __getClientManager(self): return self.__client_manager
    client_manager = property(__getClientManager)
