# TODO: Check if it's always possible to send skippable packets

from happyboom.common.log import log
from happyboom.server.gateway import Gateway
from happyboom.server.client_manager import ClientManager
import random, thread, time

class Server(object):
    def __init__(self, gateway, arg): #verbose=False, debug=False):
        self.started = False
        self.__debug = arg.get('debug', False)
        self.__verbose = arg.get('verbose', False)
        self.__stopped = False
        self.__stoplock = thread.allocate_lock()
        self.__gateway = gateway 
        gateway.server = self
        random.seed()
        self.__items = []
        
    def born(self):
        self.gateway.born()
        
    def start(self):
        if self.__verbose: log.info("[*] Starting server...")
        self.__gateway.start()
        log.info("[*] Server started")
        
        self.__stoplock.acquire()
        running = not self.__stopped
        self.__stoplock.release()
        while running:
            self.__gateway.process()
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
        if self.__verbose: log.info("[*] Stopping server...")
        self.__gateway.stop()
        log.info("[*] Server stopped")
