#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#
# Tachatte: obsursify C source code.
# Creation: 6 decembre 2005
# Author: Victor Stinner

import sys, re, random, string
PROGRAM="Tachatte"
VERSION="2005-12-06"
        
def sortThesaurusItem(a,b):
    return b.count - a.count

def sortThesaurus(thesaurus):
    sorted = []
    for item in thesaurus.values():
        sorted.append(item)
    sorted.sort(sortThesaurusItem)
    return sorted 

def count_bits(n):
    if n < 2:
        return 1
    length = 0
    n = n - 1
    while 0 < n:
        n = n/2
        length = length + 1
    return length

class Word:
    def __init__(self, old, new, need_define):
        self.old = old
        self.new = new
        self.count = 1
        self.need_define = need_define 

class Tachatter:
    def __init__(self):
        # Options
        self.encode_number = True
        self.encode_string = True
        self.encode_syntax = False 
        self.mode = "words"
        self.eat_comments = False 
        self.eat_spaces = False 
        self.sort_thesaurus = False # most used names are shorter
        self.random_thesaurus = False  # most used names are shorter
        self.obscure = \
            ["tachatte", "zob", "couille", "merde",
             "poil", "grossepute", "putain", "encule",
             "batard", "tarace", "chameau"]
        
        # Attributes
        self.uniq = 0
        self.word_generator = None
        self.word = None
        self.thesaurus={}
        self.exclude = ["if", "else", "return", "for", "while", "do"]
        self.exclude = []
        self.syntax1 = re.compile(r"[][{}();,.*=&|:?+!<>-]")
        self.syntax2 = re.compile(r"(?:[*/+-=|!]=|\+\+|--|&&|\<\<|\>\>|\|\||-\>)")
        self.syntax3 = re.compile(r"(?:(?:\<\<|\>\>)=|\.\.\.)")
        self.file = None
        self.regex_c_include = re.compile("^# *include")
        self.c_include = ""
        self.start_word = "_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.content = []

    def getContent(self, width=79):
        text = ""
        line = ""
        tmp_text = ""
        if not self.eat_spaces:
            width = None
        for item in self.content:
            if isinstance(item, Word):
                str_item = item.new
            else:
                str_item = item
#       TODO: Fix code to allow wrap       
            if width != None:
                if width <= len(line + str_item):
                    text = text + line + "\n"
                    line = ""
            line = line + str_item
        text = text + line            
        if self.eat_spaces:
            text = text.strip()+"\n"
        return text                

    def getHeaders(self):
        content = self.c_include
        values = self.thesaurus.values()
        if self.random_thesaurus:
            random.shuffle(values)
        for item in values:
            if item.need_define:
                content = content + "#define %s %s\n" % (item.new, item.old)
        return content

    def readComment(self):
        comment = "/*"
        end = 0
        while True:
            c=self.file.read(1)
            assert c != ""
            comment = comment + c
            if c == "*":
                end = 1
            elif end == 1 and c == "/":
                if not self.eat_comments:
                    self.unput(comment)
                return
            else:
                end = 0

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

    def generateWord(self, word, new_thesaurus):
        last = None
        tries = 1
        while tries < 100:
            if self.mode in ("moo", "tachatte"):
                word = self.generateWordUniq()
            elif self.mode == "shit":
                word = self.generateWordRepeat()
            elif self.mode == "letter":
                word = self.generateWordLetter()
            else:
                word = self.generateWordRandom()
            if word not in self.thesaurus \
            and word not in new_thesaurus:
                return word
            if word == last:
                break
            last = word
            tries = tries + 1
        raise Exception("No more shit!")

    def generateWordRepeat(self):
        if 1000 <= self.uniq:
            raise Exception("Too much shit! (more than %u words)" % 1000)
        start_up, start_low, repeat, end = self.word_generator
        if self.uniq & 1 == 1:
            word = start_up + repeat * (1+self.uniq/2) + end
        else:            
            word = start_low + repeat * (1+self.uniq/2) + end
        self.uniq = self.uniq + 1
        return word

    def generateWordUniq(self):
        base = len(self.word_generator)
        length = len(self.word_generator[0])
        max = base ** length 
        if max <= self.uniq:
            raise Exception("No more shit! (more than %u words)" % max)
        word = ""
        index = self.uniq
        for i in range(0,length):
            word = word + self.word_generator[index % base][i]
            index = index / base
        self.uniq = self.uniq + 1
        return word

    def generateWordLetter(self):
        up, down = self.word_generator
        if (1 << len(up)) <= self.uniq:
            raise Exception("No more shit! (more than %u words)" % (1 << len(up)))
        word = ""
        word = chr(ord('a') + self.uniq % 26)
        index = self.uniq / 26
        self.uniq = self.uniq + 1
        if index == 1:
            return "a"+word
        index = index - 1
        while 0 < index:
            word = word + chr(ord('a')+index % 26)
            index = index / 26
        return word[::-1] 

    def generateWordRandom(self):
        index = random.randint(0, len(self.obscure)-1)
        obscure = self.obscure[index]
        new = ""
        for c in obscure:
            if 70 < random.randint(0,100):
                # Take 30% of upper case
                new = new + string.upper(c)
            else:
                new = new + c
        return new                
        
    def last_is_new_line(self):
        if len(self.content) == 0:
            return None
        last = self.content[-1]
        if isinstance(last, Word):
            return False
        else:
            return last[-1] in "\r\n"

    def last_is_space(self):
        if len(self.content) == 0:
            return None
        last = self.content[-1]
        if isinstance(last, Word):
            return False
        else:
            return last[-1] in string.whitespace

    def unput(self, str):
        self.content.append(str)

    def unputWord(self, word, need_define=True):
        if word not in self.thesaurus:
            key = len(self.thesaurus)+1
            item = Word(word, None, need_define) 
            self.thesaurus[word] = item
        else:
            item = self.thesaurus[word]
            item.count = item.count + 1
        self.content.append(item)

    def processEOL(self):
        if self.word != None:
            if self.word in self.exclude:
                self.unput(self.word)
            else:
                self.unputWord(self.word)
            self.word = None

    def init(self):
        if self.mode == "letter" and not self.random_thesaurus:
            self.sort_thesaurus = True 
        if self.sort_thesaurus:
            self.random_thesaurus = False
        if self.encode_number:
            self.start_word = self.start_word + "0123456789"

    def process(self, file):
        self.init()
        self.file = file
        while True:
            c = self.file.read(1)
            if c == '':
                break

            if c in self.start_word:
                if self.word != None:
                    self.word = self.word + c
                else:
                    self.word = c
            else:
                self.processEOL()
                if c=="#":
                    line = self.file.readline()
                    macro = "#"+line
                    while re.match(r"^.*\\ *$", line.strip()) != None:
                        line = self.file.readline()
                        macro = macro + line
                    if self.regex_c_include.match(macro) != None:
                        self.c_include = self.c_include + macro 
                    else:
                        self.unput(macro)
                elif self.encode_syntax and self.syntax1.match(c) != None:
                    d = self.file.read(1)
                    e = self.file.read(1)
                    cd = c+d
                    cde = cd+e
                    if not self.last_is_space():
                        self.unput(" ")
                    if len(cde) == 3 and self.syntax3.match(c+d+e) != None:
                        self.unputWord(c+d+e)
                        self.unput(" ")
                    elif len(cd) == 2 and self.syntax2.match(c+d) != None:
                        self.unputWord(c+d)
                        self.unput(" ")
                        self.file.seek(-len(e), 1)
                    else:
                        self.unputWord(c)
                        self.unput(" ")
                        self.file.seek(-len(d+e), 1)
                elif c in ("'", "\""):
                    self.readString(c)
                elif c=="/":
                    d = self.file.read(1)
                    if d == "/":
                        line = self.file.readline()
                        if not self.eat_comments:
                            self.unput('//'+line)
                    elif d=="*":
                        self.readComment()
                    else:
                        self.unput(c)
                        self.file.seek(-1, 1)
                else:
                    if self.eat_spaces:
                        if c in string.whitespace:
                            if not self.last_is_space():
                                self.unput(" ")
                        else:
                            self.unput(c)
                    else:
                        self.unput(c)
        self.processEOL()
        self.generateThesaurus()

    def generateThesaurus(self):        
        # Compute length of thesaurus in bits
        length = count_bits( len(self.thesaurus) )
            
        # Choose uniq word generator
        if self.mode == "shit":
            self.word_generator = ("Sh", "sh", "i", "t")
        elif self.mode == "moo":
            if length<3:
                length = 3
            self.word_generator = ("M"+"O"*(length-1), "m"+"o"*(length-1))
        else:
            self.word_generator = ("TACHATTE", "tachatte")

        if self.sort_thesaurus:
            values = sortThesaurus(self.thesaurus)
        elif self.random_thesaurus:
            values = self.thesaurus.values()
            random.shuffle(values)
        else:
            values = self.thesaurus.values()
        new_words = {}
        for item in values:
            item.new = self.generateWord(item.old, new_words)
            new_words[item.new] = item

def usage():
    print "%s version %s" % (PROGRAM, VERSION)
    print ""
    print "Usage: %s [options] file.c" % (sys.argv[0])
    print
    print "Options :"
    print "\t--help            : Print this help"
    print "\t--version         : Print the software version"
    print "\t--mode=MODE       : Mode (words, moo, tachatte, letter or shit)"
    print "\t--random          : Shuffle thesaurus (default: off)"
    print "\t--eat-comments    : Eat comments (default: off)"
    print "\t--eat-spaces      : Eat white spaces (default: off)"
    print "\t--syntax=ENABLE   : Encode syntax? (default: off)"
    print "\t--number=ENABLE   : Encode numbers? (default: on)"
    print "\t--string=ENABLE   : Encode numbers? (default: on)"
    print
    print "Values for ENABLE: 0, 1, on, off, true or false."
    sys.exit(2)

def arg2bool(arg):
    arg = arg.lower()
    if arg in ("0", "off", "false"):
        return False
    if arg in ("1", "on", "true"):
        return True
    usage()        

def parseArgs(tachatte):
    import getopt

    try:
        short = ""
        long = ["help", "version", \
            "mode=", "eat-spaces", "eat-comments", "random",
            "number=", "string=", "syntax="]
        opts, args = getopt.getopt(sys.argv[1:], short, long)
    except getopt.GetoptError:
        usage()
        
    for o, a in opts:
        if o == "--help":
            usage()
        elif o == "--version":
            print "%s version %s" % (PROGRAM, VERSION)
            sys.exit(0)
        elif o == "--mode":
            if a not in ("words", "tachatte", "moo", "shit", "letter"):
                usage()
            tachatte.mode = a
        elif o == "--eat-spaces":
            tachatte.eat_spaces = True
        elif o == "--eat-comments":
            tachatte.eat_comments = True
        elif o == "--number":
            tachatte.encode_number = arg2bool(a)
        elif o == "--syntax":
            tachatte.encode_syntax = arg2bool(a)
        elif o == "--random":
            tachatte.random_thesaurus = True
        elif o == "--string":
            tachatte.encode_string = arg2bool(a)

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
