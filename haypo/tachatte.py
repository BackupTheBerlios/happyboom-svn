#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Tachatte: obsursify C source code.
# Creation: 6 decembre 2005
# Author: Victor Stinner

import sys, re, random, string

class Word:
    def __init__(self, old, new):
        self.old = old
        self.new = new

class Tachatter:
    def __init__(self, file):
        # Options
        self.encode_number = True
        self.encode_string = True
        self.obscure = \
            ["tachatte", "zob", "couille", "merde",
             "poil", "grossepute", "putain", "encule",
             "batard", "tarace", "chameau"]
        
        # Attributes
        self.word=None
        self.thesaurus={}
        self.exclude = ["if", "else", "return", "for", "while", "do"]
        self.file = file
        self.regex_c_include = re.compile("^include")
        self.c_include = ""
        self.start_word = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if self.encode_number:
            self.start_word = self.start_word + "0123456789"
        self.content = []
        self.process()

    def getContent(self):
        text = ""
        for item in self.content:
            if isinstance(item, Word):
                text = text + item.new
            else:
                text = text + item
        return text                

    def getHeaders(self):
        content = self.c_include
        for word in self.thesaurus:
            item = self.thesaurus[word]
            content = content + "#define %s %s\n" % (item.new, item.old)
        return content

    def readComment(self):
        while True:
            c=self.file.read(1)
            assert c != ""
            if c == "*":
                c = self.file.read(1)
                if c == "/":
                    return

    def readString(self, quote):
        str = quote
        while True:
            c=self.file.read(1)
            str = str + c
            assert c != ""
            if c == quote:
                break
        if self.encode_string:                
            self.unputWord(str)                
        else:
            self.unput(str)

    def process(self, c):
        if self.word != None:
            self.word = self.word + c
        else:
            self.word = c

    def generateWord(self, new_thesaurus):
        tries = 0
        while tries < 100:
            tries = tries + 1
            index = random.randint(0, len(self.obscure)-1)
            obscure = self.obscure[index]
            new = ""
            for c in obscure:
                if 70 < random.randint(0,100):
                    # Take 30% of upper case
                    new = new + string.upper(c)
                else:
                    new = new + c
            if new not in self.thesaurus \
            and new not in new_thesaurus:
                return new
        raise Exception("No more shit!")
        
    def unput(self, str):
        self.content.append(str)

    def unputWord(self, word):
        if word not in self.thesaurus:
            key = len(self.thesaurus)+1
            self.thesaurus[word] = Word(word, None) 
        self.content.append( self.thesaurus[word] )

    def processEOL(self, c):
        if self.word != None:
            if self.word in self.exclude:
                self.unput(self.word)
            else:
                self.unputWord(self.word)
            self.word = None
        if c != None:
            self.unput(c)

    def process(self):       
        while True:
            c = self.file.read(1)
            if c == '':
                break
            elif c=="#":
                line = self.file.readline()
                if self.regex_c_include.match(line) != None:
                    self.c_include = self.c_include + "#%s" % line 
                else:
                    self.unput('#'+line)
            elif c in ("'", "\""):
                self.readString(c)
            elif c=="/":
                c=f.read(1)
                if c == "/":
                    line = self.file.readline()
                    self.unput('/'+line)
                elif c=="*":
                    self.readComment()
                else:
                    f.seek(-1,1)
            elif c in self.start_word:
                if self.word != None:
                    self.word = self.word + c
                else:
                    self.word = c
            else:
                self.processEOL(c)
        self.processEOL(None)
        self.generateThesaurus()

    def generateThesaurus(self):        
        new_words = {}
        for word in self.thesaurus:
            item = self.thesaurus[word]
            item.new = self.generateWord(new_words)
            new_words[item.new] = item

def usage():
    print "Usage: %s file.c" % sys.argv[0]
    sys.exit(1)

if __name__=="__main__":
    if len(sys.argv)<2:
        usage()
    f=open(sys.argv[1])
    random.seed()
    t=Tachatter(f)
    sys.stdout.write(t.getHeaders())
    sys.stdout.write(t.getContent())
    f.close()
