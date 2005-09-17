import os

def getCreateHomeDir(subdir):
    """
    Get the home directory, and then create a subdirectory.
    Example: create ~/.subdir/ in Linux.
    
    Returns None if fails to find home directory and/or create subdirectory.
    """

    # Get user directory 
    if os.name=="nt":
        home = os.environ['USERHOME']
    else:
        subdir = "."+subdir
        home = os.environ['HOME']

    # Create happywarry directory if needed
    logdir = os.path.join(home, subdir)
    try:
        os.mkdir(logdir)
    except OSError, err:
        if err[0] != 17:
            logdir = None
    return logdir
