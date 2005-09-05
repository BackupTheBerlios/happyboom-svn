#!/usr/bin/python
# -*- coding: UTF-8 -*-
VERSION="0.0.0"
PROGRAM="HappyWarry"
import gettext

def main():
    # Ajoute APIBoom au PYTHONPATH ("../" pour l'instant)
    import sys, os
    apiboomdir = os.path.join(os.path.dirname(__file__), "..")
    sys.path.append(apiboomdir)

    # Setup log
    from common.log import log
    log.setFilename("/home/haypo/.happywarry/server-log")

    # Setup gettext
    localedir = os.path.join(os.path.dirname(__file__), "./locale")
    gettext.install('happywarry', localedir, unicode=1)

    # Create the server 
    from server.hw_server import HappyWarryServer
    server = HappyWarryServer()    
   
    # Run the server
    try:
        log.info(_("Server started."))
        server.run()
    except KeyboardInterrupt:
        log.info(_("Program interrupted (CTRL+C)."))
    server.stop()
    log.info(_("Server quit."))

if __name__=="__main__": main()
