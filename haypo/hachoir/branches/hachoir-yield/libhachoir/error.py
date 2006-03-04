import os
import config
from log import log
#import ui.ui
from tools import getBacktrace

def warning(message):
    if config.quiet:
        return
    if config.verbose or config.debug:
        message += "\n\n" + getBacktrace()
    log.warning(message)   

def error(message, backtrace=None):
    if config.verbose or config.debug:
        message += "\n\n" + getBacktrace()
    log.error(message)

