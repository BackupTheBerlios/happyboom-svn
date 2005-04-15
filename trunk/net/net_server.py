# Echo server program
import socket
import common
import thread
import threading
from server_waiter import NetworkServerWaiter

class NetworkServer(object):
	def __init__(self):
		self.waiter = NetworkServerWaiter(self)
		self.clients = []
		self.msg_handler = None
		self.on_client_connect = None
		self.on_client_disconnect = None
		self.on_read = None
		self.on_send = None
		self.on_binding_error = None
		self.clients_sema = threading.Semaphore()
		self.debug = False
		self.name = "network server"

	def start(self, port, max_connection):
		thread.start_new_thread( self.waiter.run_thread, (port,max_connection,))

	def client_connect(self, client):
		client.on_read = self.on_read
		client.on_send = self.on_send
		client.connect(self)
		self.clients_sema.acquire()
		self.clients.append(client)
		self.clients_sema.release()
		if self.on_client_connect != None: self.on_client_connect (client)

	def client_disconnect(self, client):
		if self.debug:
			print "Client %s leave server %s." \
				% (client.name, self.name)
		self.clients_sema.acquire()
		self.clients.remove(client)
		self.clients_sema.release()
		self.waiter.client_disconnect(client)
		if self.on_client_disconnect != None: self.on_client_disconnect (client)
		
	def send(self, data):
		self.clients_sema.acquire()
		for client in self.clients:	client.send(data)
		self.clients_sema.release()

	def stop(self):
		self.clients_sema.aquire()
		for client in clients: client.conn.close()
		self.clients_sema.release()
	
	def getListening(self):
		return self.waiter.listening
	listening = property(getListening)

	def getHost(self):
		return self.waiter.host
	host = property(getHost)
	
	def getPort(self):
		return self.waiter.port
	port = property(getPort)
