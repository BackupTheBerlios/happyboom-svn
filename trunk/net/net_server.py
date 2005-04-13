# Echo server program
import socket
import common
import thread
import threading

class NetworkServerClient:
	def __init__(self, conn, addr):
		self.conn = conn
		self.addr = addr
		self.net_server = None
		self.connected = False

	def getAddrStr(self):
		return "ip=%s, port=%u" % (self.addr[0], self.addr[1])
	
	def connect(self, server):
		self.net_server = server
		self.connected = True
		
	def disconnect(self):
		self.connected = False
		if self.net_server != None:
			self.net_server.client_disconnect(self)
		self.conn.close()
			
	def readNonBlocking(self, max_size=1024):
		if not self.connected: return None
		self.conn.setblocking(0)
		try:
	 		data = self.conn.recv(max_size) 
		except socket.error, error:
			if error[0] == 11: return None
			raise
		if len(data)==0:
			self.disconnect()
			return None
		return data

	def read(self, max_size=1024):
		if not self.connected: return None
	 	data = self.conn.recv(max_size) 
		if len(data)==0: return None
		return data

	def send(self, data):
		if not self.connected: return
		try:
			self.conn.send(data)
		except socket.error:
			self.disconnect()

	def stop():
		self.conn.close()
		
class NetworkServerWaitClients:
	def __init__(self, server, port):
		self.PORT = port # Arbitrary non-privileged server
		self.server = server
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.HOST = socket.gethostname() 

	def run_thread(self, max_connexion=4):
		try:
			self.start(max_connexion)
		except Exception, msg:
			print "NETWORK SERVER EXCEPTION!"
			print "ERROR MSG: %s" % (msg)

	def start(self, max_connexion=3):
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.s.bind((self.HOST, self.PORT))
		print "Server listening (host=%s)." % (self.HOST)
		self.s.listen(max_connexion)

		while 1:
			try:
				(conn, addr) = self.s.accept()
				client = NetworkServerClient(conn, addr) 
				self.server.client_connect (client)
				client = None
			except socket.error, error:
				if error[0] == 104:
					# Connexion reset by peer.
					if client != None: client.disconnect()
				else:
					raise
				

class NetworkServer:
	def __init__(self, port):
		self.waiter = NetworkServerWaitClients(self, port)
		self.clients = []
		self.msg_handler = None
		self.on_client_connect = None
		self.on_client_disconnect = None
		self.clients_sema = threading.Semaphore()

	def start(self):
		print "Start server on %s:%s." % (self.waiter.HOST, self.waiter.PORT)
		thread.start_new_thread( self.waiter.run_thread, ())

	def client_disconnect(self, client):
		print "Client %s disconnected." % (client.getAddrStr())
		self.clients_sema.acquire()
		self.clients.remove(client)
		self.clients_sema.release()
		if self.on_client_disconnect != None: self.on_client_disconnect (client)

	def client_connect(self, client):
		print "New client %s" % (client.getAddrStr())
		client.connect(self)
		self.clients_sema.acquire()
		self.clients.append(client)
		self.clients_sema.release()
		if self.on_client_connect != None: self.on_client_connect (client)

	def send(self, data):
		self.clients_sema.acquire()
		for client in self.clients:	client.send(data)
		self.clients_sema.release()

	def stop():
		self.clients_sema.aquire()
		for client in clients: client.conn.close()
		self.clients_sema.release()
