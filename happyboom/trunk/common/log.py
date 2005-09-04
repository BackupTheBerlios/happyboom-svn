#!/usr/bin/python
# -*- coding: UTF-8 -*-

import time

class Log:
    LOG_INFO   = 0
    LOG_WARN   = 1
    LOG_ERROR  = 2

    def __init__(self):
        self.__buffer = {}
        self.__file = None

    def setFilename(self, filename):
        try:
            self.__file = open(filename, "w")
        except IOError, errno:
            if errno[0] == 2:
                self.__file = None
                self.info("Log.setFilename(%s) fails : no such file." % filename)
                return
            raise

    def dump(self):
        print self.__buffer

    def getLevelPrefix(self, level):
        if level==Log.LOG_WARN: return "[warn]"
        if level==Log.LOG_ERROR: return "[error]"
        return "[info]"

    def new_message(self, level, str):
        if not self.__buffer.has_key(level):
            self.__buffer[level] = [str]
        else:
            self.__buffer[level].append(str)
        print str
        if self.__file:
            self.__file.write("%s - %s %s\n" \
                % (time.strftime("%Y-%M-%d %H:%M:%S"),
                   self.getLevelPrefix(level),
                   str))

    def info(self, str):
        self.new_message(Log.LOG_INFO, str)

    def warn(self, str):
        self.new_message(Log.LOG_WARN, str)

    def error(self, str):
        self.new_message(Log.LOG_WARN, str)

log = Log()        
