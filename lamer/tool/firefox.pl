#!/usr/bin/perl

use MIME::Base64;

$suite_serveur = 1;
$suite_id_txt = 2;
$suite_id = 3;
$suite_pass_txt = 4;
$suite_pass = 5;

sub nv_idpass {
    $user = '';
    $pass = '';
}

sub nv_site {
    $server = '';
    $ligne = 0;
    $suite = 0;
}

sub affiche {
    if ($server eq '') { return; }
    $server =~ s/ +\(.*\)$//;
#     $lg_max = 16;
#     $user =~ s/^.*(.{$lg_max})$/(...)\1/ if ($lg_max<length($user));
#     $pass =~ s/^.*(.{$lg_max})$/(...)\1/ if ($lg_max<length($pass));
    print ("S=$server, U=$user, P=$pass\n");
}

nv_site();
nv_idpass();
open(FILE, $ARGV[0]);
while (<FILE>) {
    chomp();
    next if (/^\#/);

SWITCH: {
    $suite++;
    if (/^\./) { nv_site(); last SWITCH; }
    if ($suite == $suite_serveur) { $server = $_; last SWITCH; }
    if ($suite == $suite_id) { $user = $_; last SWITCH; }
    if ($suite == $suite_pass) { 
	$pass = $_; 
	$suite = $suite_id_txt-1; 
	affiche();
	nv_idpass();
	last SWITCH; 
    }
}

    $ligne++;
}
close(AUTOCOMPLETE);
