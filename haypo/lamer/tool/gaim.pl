#!/usr/bin/perl

use XML::Simple;

my $file = $ARGV[0];
my $xs1 = XML::Simple->new();
my $doc = $xs1->XMLin($file);

%accounts = %{$doc->{account}};

%human_protocol = (
	'prpl-oscar' => "ICQ",
	'prpl-yahoo' => "Yahoo",
	'prpl-jabber' => "Jabber",
	'prpl-msn' => "MSN"
);

foreach my $key (keys %accounts){
    $user = $key;
    $item = $accounts{$key};
    $protocol = $item->{protocol};
	$protocol = $human_protocol{$protocol} if exists $human_protocol{$protocol};
	
    $pass = ($item->{password});
    $pass = $pass ? '"'.$pass.'"' : "<unknow>"; 
	
    print "$protocol : $user : $pass\n";
}
