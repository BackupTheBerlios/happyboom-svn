#!/usr/bin/python
# -*- coding: UTF-8 -*-
VERSION="0.0.0"
PROGRAM="HappyWarry"


def main():
    # Ajoute APIBoom au PYTHONPATH ("../" pour l'instant)
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

    # Cree le systeme de log
    from common.log import log
    log.setFilename("/home/haypo/.happywarry/server-log")

    # Instancie une serveur
    from server.hw_server import HappyWarryServer
    server = HappyWarryServer()    

    try:
        log.info("Server started.")
        server.run()
    except KeyboardInterrupt:
        log.info("Program interrupted (CTRL+C).")
    server.stop()
    log.info("Server quit.")

if __name__=="__main__": main()
