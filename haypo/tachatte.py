#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Tachatte: obsursify C source code.
# Creation: 6 decembre 2005
# Author: Victor Stinner

import sys, re, random, string
PROGRAM="Tachatte"
VERSION="2005-12-06"

class Word:
    def __init__(self, old, new):
        self.old = old
        self.new = new

class Tachatter:
    def __init__(self):
        # Options
        self.encode_number = True
        self.encode_string = True
        self.reversible = False
        self.obscure = \
            ["tachatte", "zob", "couille", "merde",
             "poil", "grossepute", "putain", "encule",
             "batard", "tarace", "chameau"]
        
        # Attributes
        self.uniq = 1
        self.word = None
        self.thesaurus={}
        self.exclude = ["if", "else", "return", "for", "while", "do"]
        self.file = None
        self.regex_c_include = re.compile("^include")
        self.c_include = ""
        self.start_word = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if self.encode_number:
            self.start_word = self.start_word + "0123456789"
        self.content = []

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
        if not self.reversible:
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

    def generateWordReversible(self, new_thesaurus):
        self.uniq = self.uniq + 1
        if 256 <= self.uniq:
            raise Exception("No more shit!")
        up="TACHATTE"
        down="tachatte"
        word = ""
        index = self.uniq
        for i in range(0,8):
            if (index & 1 == 1):
                word = word + up[i]
            else:
                word = word + down[i]
            index = index/2
        return word     

    def generateWordRandom(self, new_thesaurus):
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

    def process(self, file):
        self.file = file
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
            if self.reversible:
                item.new = self.generateWordReversible(new_words)
            else:
                item.new = self.generateWordRandom(new_words)
            new_words[item.new] = item

def usage():
    print "%s version %s" % (PROGRAM, VERSION)
    print ""
    print "Usage: %s [options] file.c" % (sys.argv[0])
    print
    print "Options :"
    print "\t--help            : Print this help"
    print "\t--version         : Print the software version"
    print "\t--reversible      : Use reversible mode"
    sys.exit(2)

def parseArgs(tachatte):
    import getopt

    try:
        short = ""
        long = ["help", "version", \
            "reversible"]
        opts, args = getopt.getopt(sys.argv[1:], short, long)
    except getopt.GetoptError:
        usage()
        
    for o, a in opts:
        if o == "--help":
            usage()
        if o == "--version":
            print "%s version %s" % (PROGRAM, VERSION)
            sys.exit(0)
        if o == "--reversible":
            tachatte.reversible = True

    if len(args) != 1:
        usage()

    return args[0]

if __name__=="__main__":
    if len(sys.argv)<2:
        usage()

    # Prepare
    t=Tachatter()
    filename = parseArgs(t)
    random.seed()

    # Process file
    file = open(filename)
    t.process(file)

    # Display result
    sys.stdout.write(t.getHeaders())
    sys.stdout.write(t.getContent())
