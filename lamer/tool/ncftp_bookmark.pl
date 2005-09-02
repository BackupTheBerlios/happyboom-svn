#!/usr/bin/perl
# Decode ncftp bookmark file

use MIME::Base64;

while ($input = <STDIN>) {
  if (! $input eq '') {
    chop $input;
    @tab = split(/,/, $input);
    $id = $tab[2];
    $server = $tab[1];
    $pass = $tab[3];
    $port = $tab[7];
    if ( $pass =~/\*encoded\*/ ) {
      $pass=~s/\*encoded\*//;
      $pass = decode_base64($pass);
    }
    $pass =~ s/\0+$//;
    print ("ftp://$id:$pass\@$server:$port/\n");
  }
}

