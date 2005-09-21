#
# Set SMTP server in Evolution configuration using gconftool-2 tool
# and parser XML files (from gconf).
# Author: Victor Stinner
# 15 august 2005
#

import os, sys, re

def getAccounts():
	out = os.popen("gconftool-2 --get /apps/evolution/mail/accounts")
	raw = out.read()
	
	data = raw[1:-3]
	data = data.split("\n")

	accounts = []
	for i in range(0,len(data)-1,2):
		if 0 < i:
			accounts.append( data[i][1:] + data[i+1] )
		else:
			accounts.append( data[i] + data[i+1] )
	
	return (raw, accounts,)
	
def changeSmtp(content, new_smtp_url):
	import xml.dom.minidom
	doc = xml.dom.minidom.parseString(content)
	transports = doc.getElementsByTagName("transport")
	urls = transports[0].getElementsByTagName("url")
	urls[0].childNodes[0].data = new_smtp_url
	return doc.toxml("UTF-8")

def extractXmlHeader(content):
	r = re.compile(r'^(<\?xml version="1\.0" encoding="UTF-8"\?>)\n(.*)$')
	m = r.match(content)
	if m == None:
		print "Erreur XML pour %s" % (content)
		sys.exit(1)
	return (m.group(1), m.group(2), )

def escape(text):
	import re
	text = re.sub(r"([\"'\\])", r"\\\1", text)
#	text = text.replace("\n", "\\\\n")
#	text = text.replace("\r", "\\\\r")
	return text 
	
def saveAccounts(accounts):
	key = "/apps/evolution/mail/accounts"
	cmd  = "/usr/bin/gconftool-2 "
	cmd += "--type=list "
	cmd += "--list-type=string "
	cmd += "--set /apps/evolution/mail/accounts "
	cmd += '"'+escape(accounts)+'"'
	stdin, stdout, stderr = os.popen3(cmd)
	err = stderr.read()
	if err != "":
		print "Erreur :\n%s" % (err)
		sys.exit(1)

def convertAccounts(accounts):
	old_accounts = accounts
	accounts = []
	for account in old_accounts:
		accounts.append( extractXmlHeader(account) )
		
	out = "["+accounts[0][0]+"\n"+accounts[0][1]
	del accounts[0]
	for account in accounts:
		out = out + "\n,"+account[0]+"\n"+account[1]
	out = out + "\n]"
	return out

def backupAccounts(raw):
	f = open("/home/haypo/1backup/evolution_old_accounts.yyy", "w")
	f.write(raw)
	f.close()

def main():
	if len(sys.argv)<2:
		print "Usage: %s SERVER" % sys.argv[0]
		sys.exit(1)
	smtp = sys.argv[1]
    email = "victor.stinner%40utbm.fr"

	try:
		print "Set Evolution STMP to %s." % (smtp)
		
		url = "smtp://"+email+"@"+smtp+"/;use_ssl=never"	
		raw, accounts = getAccounts()
#		backupAccounts(raw)
		for i in range(len(accounts)):
			accounts[i] = changeSmtp(accounts[i], url)
		raw2 = convertAccounts(accounts)
		saveAccounts(raw2)
		print "Done."
		
	except Exception, err:
		print "Exception", err

if __name__=="__main__": main()
