from net import io, io_udp, io_tcp, net_buffer
from pysma import Kernel, DummyScheduler, ActionAgent, ActionMessage
import re, random, thread, traceback, time

class HappyBoomAgent(ActionAgent):
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

class HappyBoomPacker:
    """
    Pack arguments to binary string.
    """
    def __init__(self):
        pass

    def packUtf8(self, data):
        return data.encode("utf-8")

    def packBin(self, data):
        return data

    def pack(self, datalist):
        out = ""
        for type,data in datalist:
            # TODO: Use dict instead of long if list
            if type=="bin":
                data = self.packBin(data)
            elif type=="utf8":
                data = self.packUtf8(data)
            else:
                raise HappyBoomPackerException("Wrong argument type: %s" % type)
            out = out + data
        return out        

class HappyBoomGateway(HappyBoomAgent):
    def __init__(self, server, arg):
        self.__server = server
        HappyBoomAgent.__init__(self, "gateway")
        self.nextChar = None
        self._debug = arg.get("debug", False)
        self._verbose = arg.get("verbose", False)
        Kernel().addAgent(DummyScheduler(sleep=0.01))
        self.packer = HappyBoomPacker()

    # Convert a (role,type,arg) to string (to be sent throw network)
    def createMsg(self, role, function, args=None):
        if args != None:
            return "%s:%s:%s" % (role, type, args)
        else:
            return "%s:%s" % (role, type)

    def pack(self, datalist):
        return self.packer.pack(datalist)

    def sendMsgToClient(self, msg, client):
        client.send(io.Packet(msg))

    def start(self):
        Kernel.instance.addAgent(self)
        
    def stop(self):
        Kernel.instance.stopKernel()

    def sendText(self, txt, client=None):
        if client != None:
            msg = self.createMsg("agent_manager", "Text", txt)
            client.send(io.Packet(msg))
        else:
            self.sendNetworkMessage("agent_manager", "Text", txt)

    def sendNetworkMessage(self, role, type, arg=None, skippable=False):
        msg = self.createMsg(role, type, arg)
        clients = self.__server.client_manager.supported_features.get(role, ())
        for client in clients:
            client.send (io.Packet(msg, skippable=skippable))

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
        
    def recvClientPacket(self, packet):
        self.__buffer.append(packet.recv_from.addr, packet)

    def stop(self):
        self.__gateway.sendNetworkMessage("game", "Stop", skippable=True)
        self.__io.stop()

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
        
        arg = self.__gateway.pack((("utf8", u"Lost connection"),))
        msg = self.__gateway.createMsg("presentation", "bye", arg)
        self.__gateway.sendMsgToClient(msg, client)
        
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

    def __do_openClient(self, client):
        if self.__verbose: print "[*] Display %s try to connect ..." % (client.name)
        
#        self.__buffer.clear(client.addr)
       
        # Check protocol version (max: wait 200ms)
        answer = self.readClientAnswer(client, 0.200)
        if answer != self.__protocol_version:
            # If it isn't the right version, send presention.bye(...)
            txt = u"Sorry, you don't have same protocol version (%s VS %s)" \
                % (answer, self.__protocol_version)
            msg = self.__gateway.createMsg("presentation", "bye", txt.encode("UTF-8"))
            self.__gateway.sendMsgToClient(msg, client)

            # Wait 0.5s and then disconnect the client
            time.sleep(0.500)
            client.disconnect()
            return
            
        # Send protocol version with "hello()"
        signature = self.generateSignature()
        arg = self.__gateway.pack("bin", self.__protocol_version,"bin", signature)
        msg = self.__gateway.createMsg("presentation", "hello", arg)
        self.__gateway.sendMsgToClient(msg, client)
         
        # Read features (max: wait 1sec)
        answer = self.readClientAnswer(client, 1.0)
        #TODO: do something with answer :-)

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
