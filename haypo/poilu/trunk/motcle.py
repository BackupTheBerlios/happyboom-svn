#! /usr/bin/env python
# -*- coding: utf-8      -*-

import re
import random
import codecs

def unicode2term(str): 
	return str.encode("latin-1")

class motcle_poilu:
    def __init__(self):
		self.insulte = dict()
		self.regex = dict() 
		self.charge_regex()
		self.charge()

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
        self.insulte = {}
        for ligne in f:
			ligne = unicode(ligne.strip(), "utf8")
			regs = re.compile("^([^:]+):(.+)$").search(ligne)
			if regs != None: self.ajoute(regs.group(1), regs.group(2))
        f.close()

    def charge_regex(self):
        f = codecs.open("motcle_regex.txt","r","utf8")
        self.regex = dict()
        for ligne in f:
            ligne = ligne.strip()
            regs = re.compile("^([^:]+):(.+)$").search(ligne)
            if regs != None: 
                regex = re.compile(regs.group(2))
                self.regex[regs.group(1)] = regex
            else:
                print "La ligne \"%s\" de motcle_regex.txt n'a pas été comprise !" % ligne
        f.close()

    def calcule_cle(self, str):
        for key,regex in self.regex.items():
            r = regex.search(str)
            if r != None: return key 
        return None

    def reponse(self, str):
        cle = self.calcule_cle(str)
        if cle==None: return None
        if not self.insulte.has_key(cle): return None
        if len(self.insulte[cle])==0: return None
        return random.choice(self.insulte[cle])
