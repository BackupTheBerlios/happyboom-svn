#! /usr/bin/env python
# -*- coding: ISO8859-1      -*-
#
# Bot IRC poète (ou presque) basé sur un exemple de Joel Rosdahl 
# <joel@rosdahl.net>
#
# Commandes privées
# -----------------
#
#   rime <mot>           : ajoute un mot au dictionnaire des rimes
#   derime <mot>         : supprime un mot du dictinnaire des rimes
#   dit #chan (...)      : fait parler le bot
#   liste rimes <mot>    : liste toutes les rimes connues pour le nom donné
#   recharge_muet        : recharge muet.txt
#   recharge_terminaison : recharge terminaison.txt
#   recharge_insult      : charge insulte.txt
#   recharge_motcle      : charge motcle_regex.txt
#   join #<chan>         : joindre le canal #<chan>
#   backup               : sauve toutes les données sur le disque dur
#   utf-8                : passe en UTF-8
#   iso                  : passe en iso-xxx
#   muet                 : liste des caractères muets
#   taux_reponse         : affiche le taux de réponse
#   taux_reponse xx      : fixe le taux de réponse (en pourcent), 0% : ne
#                          répond jamais, 100% répond chaque fois qu'il trouve
#                          une rime
#
# Commandes publiques 
# -------------------
#   ta gueule        : Fait taire le bot
#   casse toi        : Le bot se déconnecte
#

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
        self.taux_reponse = 20
        self.welcome = u"Salut"

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)
        self.send_privmsgu(self.channel, self.welcome) 

    def get_command(self, e): 
        cmd = e.arguments()[0]
        if self.utf8_chan: 
            try:
                cmd=unicode(cmd, "utf-8")
            except:
                self.echo("Etês-vous sûr d'être en UTF-8 ?")
                cmd=unicode(cmd, "latin-1")
        else:
            cmd=unicode(cmd, "iso-8859-1")
        return cmd.strip() 

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
            if nick==self.god and self.do_priv_command(regs.group(1)): return
            self.do_pub_command(nick, regs.group(1))
            return

        # Bot désactivé ? Exit !
        if self.enmarche == 0:
            return
            
        # Sinon, cherche une rime
        cmd = cmd.lower()
        reponse = self.dico.reponse(cmd)
        if reponse==None: reponse = self.motcle.reponse(cmd)
        if reponse==None: return
        
        if self.taux_reponse <= random.uniform(0,101): return
        self.send_privmsgu(self.channel, nick+": "+reponse)
        return
            
    def send_privmsg(self, nick, message):
        if self.utf8_chan: 
            self.connection.privmsg(nick, message.decode("latin-1").encode("utf-8"))
        else:
            self.connection.privmsg(nick, message)
            
    def send_privmsgu(self, nick, message):
        if self.utf8_chan: 
            self.connection.privmsg(nick, message.encode("utf-8"))
        else:
            self.connection.privmsg(nick, message.encode("iso-8859-1"))

    def echo(self, message):
        print "%s" %( message )
        self.send_privmsg(self.god, message)
    
    def echou(self, message):
        print "%s" %( unicode2term(message) )
        self.send_privmsgu(self.god, message)

    def before_dying(self):
        self.dico.sauve()

    def do_pub_command(self, nick, cmd):
        c = self.connection

        if (re.compile("^ta gueule", re.IGNORECASE).search(cmd) != None):
            if self.enmarche!=0: self.send_privmsg(self.channel, "Ok, je me tais")
            self.enmarche = 0
        else:
            if self.enmarche==0: self.send_privmsg(self.channel, "re")
            self.enmarche = 1

    def do_priv_command(self, cmd):
        c = self.connection

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
            
        regs = re.compile("^dit (#[^ ]+) (.+)$", re.IGNORECASE).search(cmd)
        if regs != None:
            self.send_privmsgu(regs.group(1), regs.group(2))
            return True
            
        if cmd == "utf8":
            if self.utf8_chan==False: self.echo("Passe en UTF-8")
            self.utf8_chan = True
            return True

        if cmd == "iso":
            if self.utf8_chan==True: self.echo("Passe en ISO-XXXX-X")
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
            
        regs = re.compile("^taux_reponse (.*)$", re.IGNORECASE).search(cmd)
        if regs != None:
            try:
                taux = int(regs.group(1))
                if taux<0: taux=0
                if 100<taux: taux=100
                self.taux_reponse = taux
                self.echou(u"Taux réponse = %s" % self.taux_reponse)
                return True
            except:
                self.echou(u"%s n'est pas un taux valide" %(regs.group(1)))
            
        if cmd=="taux_reponse":
            self.echo ("Taux réponse = %s" %(self.taux_reponse) )
            return True

        if cmd=="muet":
            self.echou(self.dico.muet)
            return True

        if (cmd == "recharge_muet"):
            self.echo("(recharge muet.txt)")
            self.dico.charge_muet()
            return True
            
        if (cmd == "recharge_terminaison"):
            self.echo("(recharge terminaison.txt)")
            self.dico.charge_regex()
            return True
            
        if (cmd == "recharge_motcle"):
            self.echo("(recharge motcle_regex.txt)")
            self.motcle.charge_regex()
            return True
            
        if (cmd == "recharge_insulte"):
            self.echo("(recharge insulte.txt)")
            self.motcle.charge()
            return True
            
        if (cmd == "backup"):
            self.dico.sauve()
            self.echo("backup done.")
            return True
             
        regs = re.compile("^join (#.*)$", re.IGNORECASE).search(cmd)
        if regs != None:
            self.channel = regs.group(1) 
            self.connection.join(self.channel)
            return True
        return None

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
        print "Interrompu (CTRL+C)."

if __name__ == "__main__":
    main()


