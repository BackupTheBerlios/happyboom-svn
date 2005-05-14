import socket
import threading
import traceback
from io_client import IO_Client

class NetworkServerWaiter(object):
	def __init__(self, server):
		self.__server = server
		self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.__port = None
		self.__host = ''
		self.__max_clients = None
		self.__nb_clients = 0
		self.__nb_clients_sema = threading.Semaphore()
		self.__listening = False
		self.__listening_sema = threading.Semaphore()
		self.__running = False

	def isRunning(self):
		return self.__running

	def run_thread(self, port, max_connection):
		try:
			self.__running = True
			self.start(port, max_connection)
		except Exception, msg:
			print "NETWORK SERVER EXCEPTION!"
			print "ERROR MSG: %s" % (msg)
		traceback.print_exc()
		self.__running = False 
		
	def clientConnect(self, client):
		if self.__server.debug:
			print "Client %s enter server %s." \
				% (client.name, self.__server.name)
		self.__nb_clients_sema.acquire()
		self.__nb_clients = self.__nb_clients + 1
		self.__nb_clients_sema.release()
		self.__server.clientConnect (client)

	def clientDisconnect(self, client):
		if self.__server.debug: print "New client : %s" % (client.getName())
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
				print "Client %s refused on server %s (too many connection, %u/%u)." \
					% (addr, self.__server.name, \
					   self.getNbClients(), self.__max_clients)
			conn.close()
			return None
		return IO_Client(self.__server, addr, conn=conn)

	def start(self, port, max_connection):
		self.__max_clients = max_connection
		self.__port = port
		if self.__server.debug: 
			print "Start %s on port %u." \
				% (self.__server.name, port)
		self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		try:
			self.__socket.bind((self.__host, self.__port))
			self.__socket.listen(max_connection)
		except socket.error, err:
			if self.__server.debug:
				print "Binding error for %s." % (self.__server.name)
			if self.__server.on_binding_error != None:
				self.__server.on_binding_error (self.__server)
			return
		if self.__server.debug: 
			print "Server %s is listening (max=%u clients)." \
				% (self.__server.name, max_connection)
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
