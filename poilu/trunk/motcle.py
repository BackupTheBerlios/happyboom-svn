#! /usr/bin/env python
# -*- coding: utf-8      -*-

import re
import random

def unicode2term(str): 
	return str.encode("latin-1")

class motcle_poilu:
    def __init__(self):
		print "init motcle."
		self.insulte = dict()
		self.regex = []
		print "regex = ", self.regex
		self.charge_regex()
		print "regex = ", self.regex
		self.charge()
		print "regex = ", self.regex

    def echo(self, message):
        print message
		
    def ajoute(self, cle, reponse):
        if self.insulte.has_key(cle):
            if terme in self.dico[cle]: return None
            self.insulte[cle].append(reponse)			
        else:
            self.insulte[cle] = [reponse]
        return True

    def supprime(self, cle, reponse):
        if not self.dico.has_key(cle): return None
        if not terme in self.dico[cle]: return None
        self.echo ("Supprime l'insulte %s" %(reponse))
        self.dico[fin].remove(reponse)
        return True

    def insultes(self,cle):
        if not self.dico.has_key(cle): return []
        return self.dico[cle]

    def sauve(self):
        self.echo ("Sauve les insultes.")
        f = file("insulte.txt", "w")
        for cle in self.insulte:
			cle_utf8 = cle.encode("utf-8")
			for reponse in self.insulte[cle]: 
				f.write ("%s:%s\n" %(cle_utf8, terme.encode("utf-8")))
        f.close()
		
    def charge(self):
        f = file("insulte.txt","r")
        for ligne in f:
			ligne = unicode(ligne.strip(), "utf8")
			regs = re.compile("^(.+):(.+)$").search(ligne)
			if regs != None: self.ajoute(regs.group(1), regs.group(2))
        f.close()

    def charge_regex(self):
        print "Charge les regex"
        self.regex = []
        f = file("motcle_regex.txt","r")
        for ligne in f:
            ligne = unicode(ligne.strip(), "utf8")
            regs = re.compile("^(.+):(.+)$").search(ligne)
            if regs != None: 
                print "Ajoute ", ligne
                regex = re.compile(regs.group(2))
                self.regex.append( (regs.group(1), regex,) )
        f.close()

    def calcule_cle(self, str):
        print "regex = ", self.regex
        print "la"
        for item in self.regex:
            r = regex.search(item[1])
            if r != None: return item[0] 
        return None

    def reponse(self, str):
        print "regex = ", self.regex
        print "Self = ", self
        print "str = ", str
        cle = self.calcule_cle(str)
        if cle==None: return None
        if not self.insulte.has_key(cle): return None
        if len(self.insulte[cle])==0: return None
        return random.choice(self.insulte[cle])
