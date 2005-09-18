import curses

def convertXY(window, x, y):
    #global window
    maxy, maxx = window.getmaxyx()
    x = int(x * maxx / 640)
    y = int(y * maxy / 350)
    return x, y

def onLogMessage(level, prefix, message):
    window.addstr(message+"\n")

window = None
