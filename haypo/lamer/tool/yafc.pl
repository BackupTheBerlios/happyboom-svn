#!/usr/bin/perl

use MIME::Base64;

sub nv_site {
    $server = '';
    $user = '';
    $pass = '';
}

sub affiche {
    if ($server eq '') { return; }
    $pass = decode_base64($') if ($pass =~ /^\[base64\]/);
    print ("ftp://$user:$pass\@$server/\n");
    nv_site();
}

nv_site();
open(FILE, $ARGV[0]);
while (<FILE>) {
    chomp();
    next if (/^\#/ || /^$/);

    if ($server eq '') {
        # Ligne du serveur
        @mots = split ' ',$_;
        $server = @mots[1];
    } else {
        # Ligne du user+pass
        if (/^ +login (.*) password (.*)$/) { 
            $user=$1; 
            $pass=$2;
            affiche(); 
        } if (/^ +anonymous$/) { 
            $user="anonymous"; 
            $pass="";
            affiche(); 
        } else { 
            print ("Ligne non reconnue : $_\n"); 
        }
    }
    
}
close(AUTOCOMPLETE);
affiche();
