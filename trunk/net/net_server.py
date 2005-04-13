# Echo server program
import socket
import common
import thread
import threading
from server_waiter import NetworkServerWaiter

class NetworkServer:
	def __init__(self, port):
		self.waiter = NetworkServerWaiter(self, port)
		self.clients = []
		self.msg_handler = None
		self.on_client_connect = None
		self.on_client_disconnect = None
		self.clients_sema = threading.Semaphore()

	def start(self):
		print "Start server on %s:%s." % (self.waiter.host, self.waiter.port)
		thread.start_new_thread( self.waiter.run_thread, ())

	def client_disconnect(self, client):
		print "Client %s disconnected." % (client.getAddrStr())
		self.clients_sema.acquire()
		self.clients.remove(client)
		self.clients_sema.release()
		self.waiter.client_disconnect(client)
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
