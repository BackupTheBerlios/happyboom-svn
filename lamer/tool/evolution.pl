#!/usr/bin/perl

use MIME::Base64;

# Read all accounts
%accounts = ();
open(FILE, $ARGV[0]);
while (<FILE>) {
    chomp();
    if (/^(pop|imap):__([^@]+)@([^=_]+)=(.+)$/) { 
		$protocol = $1;
		$email = $2;
		$server = $3;
		$password = $4;
		if ($email =~ /^([^;]+);auth_(.*)$/)
		{
			$email = $1;
			$auth = $2;
			$auth = "" if ($auth =~ /^\+APOP$/);
		} else {
			$auth = "";
		}
		$password = decode_base64($password);
		$email =~ s/%40/@/;

		# Important key : skip duplicate accounts
		$key = $server . ":" . $email;
		if (not exists $accounts{$key})
		{
			$accounts{$key} = 1;
			print "$server : $email : \"$password\"\n";

#			print "Email $email\n";
#			print "- authentification: $auth\n" if (! $auth =~ /^$/);
#			print "- protocol: $protocol\n" if not($protocol =~ /^pop$/); 
#			print "- server: $server\n";
#			print "- password: $password\n";
		}
	}
}
close(FILE);
