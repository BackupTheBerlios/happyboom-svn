#!/usr/bin/perl

use Env qw(VERBOSE);

sub urlEncode {
    my ($string) = @_;
    $string =~ s/(\W)/"%" . unpack("H2", $1)/ge;
    #$string# =~ tr/.//;
    return $string;
 }

sub nv_site {
    $server = '';
    $user = '';
    $pass = '';
    $port = 21;
}

sub affiche {
    return if ($user =~ /^anonymous$/);

    # Décode le mode de passe
    $dir = '.';
    $pass = `$dir/tool/gftp_descramble '$pass'`;
    chop $pass;

    # Encode l'user et pass
    $user = urlEncode($user);
    $pass = urlEncode($pass);

    # Affiche le FTP
    print ("ftp://$user:$pass\@$server");
    print (":$port") if ($port != 0 && $port != 21);
    print ("/\n");
}

$i = 1;
nv_site();
open(FILE, $ARGV[0]);
while (<FILE>) {
    $i++;
    chomp();
    push(@tab,$_);

    if (/^\[/ && $server) { affiche(); nv_site(); }
    if (/^hostname=/) { $server = $'; }
    if (/^port=/) { $port = $'; }
    if (/^username=/) { $user = $'; }
    if (/^password=/) { $pass = $'; }
}
close(AUTOCOMPLETE);

affiche();
