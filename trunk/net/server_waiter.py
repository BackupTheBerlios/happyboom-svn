import socket
import threading
from server_client import NetworkServerClient

class NetworkServerWaiter:
	def __init__(self, server, port):
		self.port = port
		self.server = server
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.host = ''
		self.nb_clients = 0
		self.nb_clients_sema = threading.Semaphore()

	def run_thread(self, max_connexion=2):
		try:
			self.start(max_connexion)
		except Exception, msg:
			print "NETWORK SERVER EXCEPTION!"
			print "ERROR MSG: %s" % (msg)
		
	def client_connect(self, client):
		self.nb_clients_sema.acquire()
		self.nb_clients = self.nb_clients + 1
		print "nb_clients = %s" % ( self.nb_clients )
		self.nb_clients_sema.release()
		self.server.client_connect (client)

	def client_disconnect(self, client):
		self.nb_clients_sema.acquire()
		self.nb_clients = self.nb_clients - 1
		print "nb_clients = %s" % ( self.nb_clients )
		self.nb_clients_sema.release()

	def getNbClients(self):
		self.nb_clients_sema.acquire()
		val = self.nb_clients
		self.nb_clients_sema.release()
		return val

	def start(self, max_connexion):
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.s.bind((self.host, self.port))
		print "Server listening (max=%u clients)." \
			% (max_connexion)
		self.s.listen(max_connexion)

		while 1:
			try:
				(conn, addr) = self.s.accept()
				if max_connexion <= self.getNbClients():
					conn.close()
					continue
				client = NetworkServerClient(conn, addr) 
				self.client_connect (client)
				client = None

			except socket.error, error:
				if error[0] == 104:
					# Connexion reset by peer.
					if client != None: client.disconnect()
				else:
					raise
