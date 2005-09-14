#!/usr/bin/python
# -*- coding: UTF-8 -*-

# HappyWarry game

VERSION="0.0.0"
PROGRAM="HappyWarry"
import gettext

def init():
    global log

    # Add HappyBoom to PYTHONPATH ("../" today, but should be improved)
    import sys, os
    file_dir = os.path.dirname(__file__)
    happyboomdir = os.path.join(file_dir, "../happyboom/trunk")
    sys.path.append(happyboomdir)

    # Get user directory 
    from happyboom.common.file import getCreateHomeDir
    logdir = getCreateHomeDir("happywarry")

    # Setup log filename
    from happyboom.common.log import log
    if logdir != None:
        logname = os.path.join(logdir, "server-log")    
        log.setFilename(logname)

    # Setup gettext
    localedir = os.path.join(file_dir, "locale")
    gettext.install('happywarry', localedir, unicode=1)

def main():
    global log

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
