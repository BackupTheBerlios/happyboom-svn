#!/usr/bin/python
# -*- coding: UTF-8 -*-

# HappyWarry game

VERSION="0.0.0"
PROGRAM="HappyWarry"
import gettext

def init():
    # Add APIBoom to PYTHONPATH ("../" today, but should be improved)
    import sys, os
    file_dir = os.path.dirname(__file__)
    apiboomdir = os.path.join(file_dir, "..")
    sys.path.append(apiboomdir)

    # Get user directory 
    from common.log import log
    if os.name=="nt":
        home = os.environ['USERHOME']
    else:
        home = os.environ['HOME']

    # Create happywarry directory if needed
    logdir = os.path.join(home, ".happywarry")
    try:
        os.mkdir(logdir)
    except OSError, err:
        if err[0]==17: pass
        logdir = None

    # Setup log filename
    if logdir != None:
        logname = os.path.join(logdir, "server-log")    
        log.setFilename(logname)

    # Setup gettext
    localedir = os.path.join(file_dir, "./locale")
    gettext.install('happywarry', localedir, unicode=1)

def main():
    # Initialize the application
    init()
    
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
