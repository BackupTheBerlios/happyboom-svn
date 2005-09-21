#
# Python script to parse Apache log file
# 21 septembre 2005
# Author: Victor Stinner
#

import re, time, sys, traceback

class ApacheLogParser:
    def __init__(self):
        # String like "abc" or "a\"bc" or just ""
        match_string = r"\"((?:[^\"]+|\\\")*)\""

        # Regex matching one line
        regex  = r"^([^ ]+) " # Origin
        regex += r"([^ ]+) " # Host
        regex += r"([a-z]+|-) " # User
        regex += r"\[([^]]+)\] " # Date
        regex += r"\"(POST|GET|HEAD) ([^ ]+) HTTP/1\.[01]\" " # Method, Url 
        regex += r"([0-9]{3}) ([0-9]+|-) " # Code, Size
        regex += match_string+" " # Referrer
        
        match_string = r"\"([^\"]*)\""
        regex += match_string+"$" # Browser string
        
        self._regex = re.compile(regex)
        print "Pattern: %s" % self._regex.pattern
        self.handler = self.processLine

    def processLine(self, line_number, line, info):
        print "Line %u: %s %s" % (line_number, info["method"], info["url"])

    def parseLine(self, line_number, line):
        try:
            print "LINE %u ========= %s =======" % (line_number, line)
            print "Regex."
            m = self._regex.search(line)
            if m == None:
                print "Can't parse line %u:\n%s" % (line_number, line)
                return
            print "Assign."
            origin, host, user, date, method, url, code, size, referrer, browser = m.groups()
            kw = { \
                "origin": origin,
                "host": host,
                "user": user,
                "date": date,
                "method": method,
                "url": url,
                "code": int(code),
                "size": size,
                "referrer": referrer,
                "browser": browser}
            print "Handler."
            self.handler(line_number, line, kw)
            print "Done."
        except KeyboardInterrupt:
            print "Interrupt line: %s" % line
            raise

    def parseFile(self, filename):
        f = open(filename, "r")

        data = f.read()
        data = data.split("\n")
        if data[-1]=="": del data[-1]
        
        line_number = 1
        print "Load file %s ..." % filename
        try:
            nb_lines = len(data)
            t = time.time()
            for line in data:
                if 40800<line_number: #0.3 < time.time() - t:
                    t = time.time()
                    progress = int( (line_number-1)*100/nb_lines )
                    print "Progress: %s%% (%u on %u) - %s" % (progress, line_number, nb_lines, line)
                self.parseLine(line_number, line)
                line_number += 1
            print "File loaded."
        except KeyboardInterrupt:
            print "Load interrupted (CTRL+C)."
            traceback.print_exc()
            sys.exit(1)

    def result(self):
        return self.origin

class ApacheLogParser_Stat(ApacheLogParser):
    def __init__(self, host):
        ApacheLogParser.__init__(self)
        self.host = host
        self.regex_host = re.compile("^"+host+"(.*)$")
        self.stat_page = {}
        self.stat_referrer = {}
        self.ignore_handler = None
        
    def hit(self, attr, key):
        if key in attr:
            attr[key] = attr[key] + 1
        else:
            attr[key] = 1

    def processLine(self, line_number, line, info):
        url = info["url"]
        code = info["code"]
        referrer = info["referrer"]
        
        # Clean url (remove hostname)
        m = self.regex_host.match(url)
        if m != None:
            url = "/"+m.group(1)

        # Ignore this hit?
#        if self.ignore_handler:
#            if self.ignore_handler(info)==True: return

        # Page hit stat
        if code not in [302, 404]:
            self.hit(self.stat_page, url)
            if referrer != "-":
                self.hit(self.stat_referrer, referrer)

    def _sort_value(self, val1, val2):
        if val1 > val2:
            return -1
        elif val1 == val2:
            return 0
        else:
            return 1

    def _sort_stat_referrer(self, key1, key2):
        return self._sort_value(self.stat_referrer[key1],  self.stat_referrer[key2])

    def _sort_stat_page(self, key1, key2):
        return self._sort_value(self.stat_page[key1],  self.stat_page[key2])

    def getTopReferrer(self, max=30, ignores=[]):
        return self.getTop(self.stat_referrer, self._sort_stat_referrer, max, ignores)
        
    def getTopPage(self, max=30, ignores=[]):
        return self.getTop(self.stat_page, self._sort_stat_page, max, ignores)
        
    def getTop(self, attr, sort_func, max=30, ignores=[]):
        keys = attr.keys()
        keys.sort(sort_func)
        top = []
        cpt = 1
        for key in keys:
            ok = True
            for ignore in ignores:
                m = ignore.search(key)
                if m != None:
                    ok = False
                    break
            if ok:
                top.append( (attr[key], key,) )
                cpt += 1
                if max < cpt: break
        return top

def printTopPage(r, max):
    # Top pages
    pages = r.getTopPage(max)
    for page in pages:
        print "%u hit(s): %s" % (page[0], page[1])

# Regex google hosts
def googleHosts():        
    return ["216\.239\.59\.104", \
        "66\.249\.93\.104", "66.102.9.104", \
        "216.109.124.98", "(images|www)\.google\.(fr|com)"]

def yahooHosts():
    return ["[a-z]+.search.yahoo.com"]

def printTopReferrer(r, max):
    # Top pages
    pages = r.getTopReferrer(max)
    for page in pages:
        print "%u hit(s): %s" % (page[0], page[1])

class HaypoCALC:
    def __init__(self):
        hosts = ["(www\.)?haypocalc\.com"] # Haypocalc
        hosts += googleHosts()
        hosts += yahooHosts()
        self.ignore_referrer = [ re.compile(r"^http://("+"|".join(hosts)+")")  ]

        self.ignore_url = []
        end = r"(\?.*)?$"
        ignore_ext = ["css", "jpg", "JPG", "png", "js", "gif", "swf"]
        ignore_ext = "|".join(ignore_ext)
        self.ignore_url.append( re.compile(r"\.("+ignore_ext+r")"+end) )
        self.ignore_url.append( re.compile(r"^/wiki/index.php\?.*&action=raw") )
        self.ignore_url.append( re.compile(r"^/robots\.txt$") )

    def ignoreHandler(self, info):
        referrer = info["referrer"]
        for regex in self.ignore_referrer:
            if regex.search(referrer) != None: return True
        return False

def usage():
    print "Usage: %s filename" % (sys.argv[0])

def main():
    try:
        if len(sys.argv)<2:
            usage()
            sys.exit(1)
        h=HaypoCALC()
        filename = sys.argv[1]
        r=ApacheLogParser_Stat("haypocalc.com")
        r.ignore_handler = h.ignoreHandler
        r.parseFile(filename)
    #    printTopPage(r, 10)
        printTopReferrer(r, 100)
    except KeyboardInterrupt:
        print "Program interrupted (CTRL+C)."
        

if __name__=="__main__": main()    
