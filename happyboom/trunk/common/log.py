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
        """
        Use a file to store all messages. The
        UTF-8 encoding will be used. Write an informative
        message if the file can't be created.

        @param filename: C{L{string}}
        """

        try:
            import codecs
            self.__file = codecs.open(filename, "w", "utf-8")
        except IOError, errno:
            if errno[0] == 2:
                self.__file = None
                self.info("Log.setFilename(%s) fails : no such file." % filename)
                return
            raise

    def getLevelPrefix(self, level):
        """
        String prefix which depends on message level.
        Eg. information returns "[info]".
        @return: C{str}
        """
        if level==Log.LOG_WARN: return "[warn]"
        if level==Log.LOG_ERROR: return "[err] "
        return "[info]"

    def new_message(self, level, str):
        """
        Write a new message : append it in the buffer,
        display it to the screen (if needed), and write
        it in the log file (if needed).

        @param level: Message level.
        @type level: C{int}
        @param str: Message content.
        @type str: C{str}
        """
        
        if not self.__buffer.has_key(level):
            self.__buffer[level] = [str]
        else:
            self.__buffer[level].append(str)
        prefix = self.getLevelPrefix(level)            
        print "%s %s" % (prefix, str)
        if self.__file:
            self.__file.write(u"%s - %s %s\n" \
                % (time.strftime("%Y-%M-%d %H:%M:%S"),
                   prefix, str))

    def info(self, str):
        """
        New informative message.
        @type str: C{str}
        """
        self.new_message(Log.LOG_INFO, str)

    def warning(self, str):
        """
        New warning message.
        @type str: C{str}
        """
        self.new_message(Log.LOG_WARN, str)

    def error(self, str):
        """
        New error message.
        @type str: C{str}
        """
        self.new_message(Log.LOG_WARN, str)

log = Log()        
