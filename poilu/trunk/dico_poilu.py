#! /usr/bin/env python
# -*- coding: ISO8859-1      -*-

import re
import random

def unicode2term(str): 
    import sys
    return str.encode(sys.stdout.encoding)

class dico_poilu:
    def __init__(self, bot):
        self.bot = bot
        self.dico = {}
        self.regex = []
        self.muet = " "
        self.charge_regex()
        self.charge_muet()
        self.charge_dico()

    def echou(self, message):
        self.bot.echou(message)
        
    def echo(self, message):
        self.bot.echo(message)
        
    def ajoute_terme(self, terme):
        cle = self.terminaison(terme)
        if cle==None: return None
        if self.dico.has_key(cle):
            if terme in self.dico[cle]: return None
            self.dico[cle].append(terme)
        else:
            self.dico[cle] = [terme]
        return True

    def supprime_terme(self, terme):
        fin = self.terminaison(terme)
        if fin==None: return None
        if not self.dico.has_key(fin): return None
        if not terme in self.dico[fin]: return None
        self.echou(u"Supprime le mot %s" %(terme))
        self.dico[fin].remove(terme)
        return True

    def termes(self,terme):
        fin = self.terminaison(terme)
        if fin==None: return
        if not self.dico.has_key(fin): return []
        return self.dico[fin]

    def sauve(self):
        self.echo ("Sauve le dico.")
        f = file("dico.txt", "w")
        dico = []
        for key in self.dico:
            for terme in self.dico[key]: 
                dico.append(terme)
        dico.sort()
        for item in dico:
            f.write ("%s\n" %(item.encode("utf-8")))
        f.close()

    def charge_dico(self):
        f = file("dico.txt","r")
        self.dico = {}
        for ligne in f:
            ligne = unicode(ligne.strip(), "utf8")
            if ligne != '': self.ajoute_terme(ligne)
        f.close()

    def charge_regex(self):
        self.regex = []
        f = file("terminaison.txt","r")
        for ligne in f:
            ligne = unicode(ligne.strip(), "utf8")
            a = ligne.split(':')
            if len(a)==2: self.regex.append(a)
        f.close()

    def charge_muet(self):
        f = file("muet.txt","r")
        self.muet = " "
        for ligne in f:
            ligne = unicode(ligne.strip(), "latin-1")
            self.muet += ligne
        f.close()

    def terminaison(self, str):
        str = unicode.rstrip(str.lower(), self.muet)
        for item in self.regex:
            fin = item[0]
            expr = item[1]
            if re.compile(expr).search(str) != None: return fin
        self.echou(u"Je n'ai pas trouvé la terminaison de \"%s\" !" %( str ))
        return None 

    def reponse(self, str):
        fin = self.terminaison(str)
        if fin==None: return None
        if not self.dico.has_key(fin): return None
        if len(self.dico[fin])==0: return None
        x = random.choice(self.dico[fin])
        if re.compile("[sx]$").search(x)!=None:
            return "Poils aux "+x
        else:
            return "Poils au "+x

