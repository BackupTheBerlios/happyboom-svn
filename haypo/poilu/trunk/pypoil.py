#! /usr/bin/env python
# -*- coding: ISO8859-1      -*-
#
# Bot IRC poète (ou presque) basé sur un exemple de Joel Rosdahl 
# <joel@rosdahl.net>
#
# Commandes privées
# -----------------
#
#  Tapez "aide" pour obtenir l'aide ;-) (ou voir la fonction aide ci-dessous)
#
# Commandes publiques 
# -------------------
#   ta gueule        : Fait taire le bot
#   casse toi        : Le bot se déconnecte
#

import types
import string, random, re
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, ip_numstr_to_quad, ip_quad_to_numstr
from motcle import *
from dico_poilu import *
from dico_poilu import unicode2term 

class TestBot(SingleServerIRCBot):
    def __init__(self, channel, utf8_channel, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.god = "haypo"
        self.channel = channel
        self.enmarche = 1
        self.utf8_chan = utf8_channel
        self.dico = dico_poilu(self)
        self.motcle = motcle_poilu()
        self.taux_reponse = 100
        self.welcome = u"Salut"
        self.reponse_motcle = True
        self.reponse_dico = True

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)
        self.send_privmsgu(self.channel, self.welcome) 

    def get_command(self, e): 
        cmd = e.arguments()[0]
        try:
            cmd=unicode(cmd, "utf-8")
        except:
            cmd=unicode(cmd, "iso-8859-1")
        return cmd.strip() 

    def aide(self):
        self.echou(u"Commandes :")
        self.echou(u"- liste rimes <mot>        : liste des rimes pour la terminaison du mot spécifié")
        self.echou(u"- rime mot / derime mot    : ajoute/supprime un mot du dictinnaire")
        self.echou(u"- terminaison mot          : affiche la terminaison du mot")
        self.echou(u"- dit #chan ... / dit nick ... : fait parler le bot")
        self.echou(u"- recharge_muet            : recharge muet.txt")
        self.echou(u"- recharge_terminaison     : recharge terminaison.txt")
        self.echou(u"- recharge_dico            : recharge dico.txt")
        self.echou(u"- recharge_motcle          : recharge motcle_regex.txt")
        self.echou(u"- join #chan / leave #chan : joint/quitte le canal #<chan>")
        self.echou(u"- nick xxx                 : change de surnom")
        self.echou(u"- backup                   : sauve toutes les données sur le disque dur")
        self.echou(u"- utf-8 / iso              : parle en UTF-8 / iso-8859-1")
        self.echou(u"- muet                     : liste des caractères muets")
        self.echou(u"- taux_reponse xxx         : fixe le taux de réponse (en pourcent)")
        self.echou(u"- reponse_dico             : active/désactive la réponse du dico")
        self.echou(u"- reponse_motcle           : active/désactive la réponse des mot-clés")

    def on_privmsg(self, c, e):
        cmd = self.get_command(e)
        self.do_priv_command(cmd) 

    def on_pubmsg(self, c, e):
        self.channel = e.target()
        nick = nm_to_n(e.source())
        cmd = self.get_command(e)

        # Commande pour le bot
        regs = re.compile("^"+self.connection.get_nickname()+"[:,>]? *(.*)$", re.IGNORECASE).search(cmd)
        if regs != None:
            if nick==self.god and self.do_priv_command(regs.group(1)):
                return
            if self.do_pub_command(nick, regs.group(1)):
                return

        # Bot désactivé ? Exit !
        if self.enmarche == 0:
            return
            
        # Sinon, cherche une rime
        reponse = None
        if reponse==None and self.reponse_motcle: reponse = self.motcle.reponse(cmd)
        if reponse==None and self.reponse_dico: reponse = self.dico.reponse(cmd)
        if reponse==None: return
        
        if self.taux_reponse <= random.uniform(0,101): return
        self.send_privmsgu(self.channel, nick+": "+reponse)
        return
            
    def send_privmsg(self, nick, message):
        if type(nick)==types.UnicodeType:
            nick = nick.encode("ascii")
        if self.utf8_chan: 
            self.connection.privmsg(nick, message.decode("latin-1").encode("utf-8"))
        else:
            self.connection.privmsg(nick, message)
            
    def send_privmsgu(self, nick, message):
        if type(nick)==types.UnicodeType:
            nick = nick.encode("ascii")
        if self.utf8_chan: 
            self.connection.privmsg(nick, message.encode("UTF-8"))
        else:
            self.connection.privmsg(nick, message.encode("iso-8859-1"))

    def echo(self, message):
        self.echou(message.decode("iso-8859-1"))
    
    def echou(self, message):
        print unicode2term(message)
        self.send_privmsgu(self.god, message)

    def before_dying(self):
        self.dico.sauve()

    def do_pub_command(self, nick, cmd):
        c = self.connection

        if (re.compile("^ta gueule", re.IGNORECASE).search(cmd) != None):
            if self.enmarche!=0: self.send_privmsg(self.channel, "Ok, je me tais")
            self.enmarche = 0
            return True
        elif self.enmarche==0:
            self.send_privmsg(self.channel, "re")
            self.enmarche = 1
            return True
        return False

    def do_priv_command(self, cmd):
        c = self.connection

        if cmd == "aide":
            self.aide()
            return True
            
        if cmd == "disconnect":
            self.disconnect()
            return True
            
        if (re.compile("^casse toi", re.IGNORECASE).search(cmd) != None):
            self.before_dying()
            self.die()
            return True
            
        regs = re.compile("^insulte (.+) (.+)$", re.IGNORECASE).search(cmd)
        if regs != None:
            if self.dico.ajoute(regs.group(1), regs.group(2)): 
                self.echou(u"Ajoute l'insulte %s pour %s" \
                    %(regs.group(2), regs.group(1)))
            return True
            
        regs = re.compile("^rime (.+)$", re.IGNORECASE).search(cmd)
        if regs != None:
            if self.dico.ajoute_terme(regs.group(1)): 
                self.echou(u"Ajoute la rime %s" %(regs.group(1)))
            return True
            
        regs = re.compile("^dit ([^ ]+) (.+)$", re.IGNORECASE).search(cmd)
        if regs != None:
            dit=regs.group(2)
            self.send_privmsgu(regs.group(1), regs.group(2))
            return True
            
        if cmd == "utf8":
            if self.utf8_chan==False: self.echo("Passe en UTF-8")
            self.utf8_chan = True
            return True

        if cmd == "iso":
            if self.utf8_chan==True: self.echo("Passe en ISO-8859-1")
            self.utf8_chan = False 
            return True
            
        regs = re.compile("^derime (.*)$", re.IGNORECASE).search(cmd)
        if regs != None:
            if self.dico.supprime_terme(regs.group(1)) != None:
                self.echou(u"Supprime la rime %s" %(regs.group(1)))
            return True
            
        regs = re.compile("^liste rimes (.+)$", re.IGNORECASE).search(cmd)
        if regs != None:
            termes = self.dico.termes(regs.group(1))
            if termes!=None: 
                self.echou("Rimes en %s: %s" %(regs.group(1), ", ".join(termes)))
            return True
            
        regs = re.compile("^liste insultes (.+)$", re.IGNORECASE).search(cmd)
        if regs != None:
            termes = self.motcle.insultes(regs.group(1))
            if termes!=None: 
                self.echou("Insultes pour %s: %s" \
                    %(regs.group(1), ", ".join(termes)))
            return True
            
        regs = re.compile("^reponse_dico$", re.IGNORECASE).search(cmd)
        if regs != None:
            self.reponse_dico = not self.reponse_dico
            self.echou(u"Réponse par dico : %s"  % self.reponse_dico)
            return True
            
        regs = re.compile("^reponse_motcle$", re.IGNORECASE).search(cmd)
        if regs != None:
            self.reponse_motcle = not self.reponse_motcle
            self.echou(u"Réponse par mot-clé : %s"  % self.reponse_motcle)
            return True
            
        regs = re.compile("^taux_reponse (.*)$", re.IGNORECASE).search(cmd)
        if regs != None:
            try:
                taux = int(regs.group(1))
                if taux<0: taux=0
                if 100<taux: taux=100
                self.taux_reponse = taux
                self.echou(u"Taux réponse = %s%%" % self.taux_reponse)
                return True
            except:
                self.echou(u"%s n'est pas un taux valide" %(regs.group(1)))
            
        if cmd=="muet":
            self.echou(self.dico.muet)
            return True

        if (cmd == "recharge_muet"):
            self.echo("(recharge muet.txt)")
            self.dico.charge_muet()
            return True
            
        if (cmd == "recharge_dico"):
            self.echo("(recharge dico.txt)")
            self.dico.charge_dico()
            return True
            
        if (cmd == "recharge_terminaison"):
            self.echo("(sauve dico, recharge terminaison.txt puis dico.txt)")
            self.dico.sauve()
            self.dico.charge_regex()
            self.dico.charge_dico()
            return True
            
        if (cmd == "recharge_motcle"):
            self.echo("(recharge motcle_regex.txt)")
            self.motcle.charge_regex()
            self.echo("(recharge insulte.txt)")
            self.motcle.charge()
            return True
            
        if (cmd == "backup"):
            self.dico.sauve()
            self.echo("backup done.")
            return True
            
        regs = re.compile("^leave (#.*)$", re.IGNORECASE).search(cmd)
        if regs != None:
            self.channel = regs.group(1).encode("ascii")
            self.connection.part(self.channel)
            return True
             
        regs = re.compile("^nick (.*)$", re.IGNORECASE).search(cmd)
        if regs != None:
            self.connection.nick(regs.group(1))
            return True
            
        regs = re.compile("^terminaison (.*)$", re.IGNORECASE).search(cmd)
        if regs != None:
            mot = regs.group(1) 
            term = self.dico.terminaison(mot)
            if term != None:
                self.echou(u"Terminaison de %s : %s" % (mot, term))
            else:
                self.echou(u"Terminaison de %s : (aucune)" % mot)
            return True
            
        regs = re.compile("^join (#.*)$", re.IGNORECASE).search(cmd)
        if regs != None:
            self.channel = regs.group(1) 
            self.connection.join(self.channel)
            return True
        return False

def main():
    import sys
    if len(sys.argv) != 4:
        print "Usage: testbot <server[:port]> <channel>[:utf8] <nickname>"
        sys.exit(1)

    s = string.split(sys.argv[1], ":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print "Error: Erroneous port."
            sys.exit(1)
    else:
        port = 6667
        
    channel = sys.argv[2]
    regs = re.compile("^(.*):utf8$").search(channel)
    regsiso = re.compile("^(.*):iso$").search(channel)
    if regs != None:
        utf8 = True
        channel = regs.group(1)
    elif regsiso != None:
        channel = regsiso.group(1)
        utf8 = False
    else:
        utf8 = False
    
    nickname = sys.argv[3]

    print "Creation de TestBot ..."
    bot = TestBot(channel, utf8, nickname, server, port)
    print "Lance le bot ... (salon %s, serveur %s, port %s)" % (channel, server, port)
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.dico.sauve()
        print "Interrompu (CTRL+C)."

if __name__ == "__main__":
    main()


