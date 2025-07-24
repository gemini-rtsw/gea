#!/usr/bin/perl
#
# Matt Kruse
# http://mkruse.netexpress.net/
#
print "Content-type: text/html\n\n";

$tail = $ENV{'QUERY_STRING'};
$tail = $tail || 1500;

# Location of the log file in Extended Log Format
$log = "/var/log/httpd/access_log";

# Local domain name to cut out of referer info
$local = "http:/baham.hi.gemini.edu";

# -------------------------

%MONTHS=(
  'Jan','01','Feb','02','Mar','03','Apr','04','May','05','Jun','06',
  'Jul','07','Aug','08','Sep','09','Oct','10','Nov','11','Dec','12'
  );

sub ReadLog {
  $LOG=shift;
  open (LOG,"tail -$tail $LOG |") || print "ERROR: Couldn't open the log file: $LOG";

  $lineerrors=0;
LOGLOOP:  while (<LOG>) {
    unless
    (($site,$rfc931,$user,$when,$request,$status,$bytes,$from,$agent)=
    /^(\S+)\s*(\S+)\s*(\S+)\s*\[([^\]]+)]\s*\"([^\"]+)"\s*(\S+)\s*(\S+)\s*\"\s*([^\"]*)\s*\"\s*\"\s*([^\"]*)\s*\"\s*$/o)
	{ 
	$lineerrors++; 
	push (@badlines,$_);
	next; 
	}
    ($page) = ($request =~ m|[^\/]*(\S*)|);

    next if ($page =~ /\.gif/); # skip the gifs
    $site="\L$site";

    # get all the time info
    ($date,$month,$year,$hour,$min,$sec) = ($when =~ m|(..)/(...)/..(..):(..):(..):(..)|o);
    $month = $MONTHS{$month};

    $datestamp = $year . $month . $date . $hour . $min;
    unless ($first{$site}) { $first{$site} = $datestamp; }

    $datestring = "${month}/${date}\&nbsp\;${hour}:${min}";

    $from =~ s|$local||;

    # Record the browser info
    $agent{$site} = $agent;

    # Update the array for site
    $line = join("|",$datestring,$page,$status,$bytes,$from);
    push(@{$sessions{$site}},$line);
    }

  close(LOG);
  }

&ReadLog($log);

sub search_words {
	return if ($found);
	my($name) = shift;
	my($url) = shift;
	my($string) = shift;

	$old_from = $from;
	if (($from =~ /$url/i) && ($from =~ /[\?\&]$string\=/)) {
		$from =~ s|.*[\?\&]$string=([^\&]*).*|$1|;
		$from =~ s|\+| |g;
		$from =~ s/%(..)/pack("c",hex($1))/ge;
		$from = "<B><FONT COLOR=red>$name:</FONT> $from</B>";
		$old_from = "<A HREF=\"$old_from\">[Q] </A>";
		$from = $old_from . $from;
		$found=1;
		}
	}

print <<"END";
<HTML>
<HEAD><TITLE>Access Analysis</TITLE>
<STYLE>
TH { font-size: x-small; }
TD { font-size: x-small; }
A { text-decoration: none; }
</STYLE>
</HEAD>
<BODY BGCOLOR="#ffffff">
END

if ($lineerrors > 0) {
	print <<"END";
$lineerrors lines were ignored. Are you sure your log file is in the Extended Log Format?<br>
An ELF entry looks like this example:<br>
<TT><NOBR>host.domain.com - - [10/Jul/1999:12:34:56 -0500] "GET / HTTP/1.1" 200 2376 "http://referer.com" "Browser Name"</NOBR></TT>
<BR><BR>
The following lines were ignored:<br>
<tt>
END
	foreach (@badlines) {
		print "<NOBR>$_</NOBR><br>";
		}
	print "</tt><br>";
	}

print <<"END";
<TABLE BORDER=1 CELLPADDING=1 CELLSPACING=0>
END

foreach $site (sort {$first{$b} <=> $first{$a}} keys %sessions) {
print <<"END";
<TR>
<TD COLSPAN=4 BGCOLOR="#cccccc" ALIGN=LEFT>
  <B>$site</B> - $agent{$site}
</TD>
</TR>
<TR>
<TH>Date</TH>
<TH>Page</TH>
<TH>Status</TH>
<TH>Referer</TH>
</TR>
END

  foreach (@{$sessions{$site}}) {
	($date,$page,$status,$bytes,$from) = split(/\|/,$_);

	# Search keywords
	$found=0;
	if ($from =~ /\?/) {  # Query results?
		&search_words("Excite","excite.com","search");
		&search_words("Excite","excite.com","FI_1");
		&search_words("Excite","excite.com","s");
		&search_words("AOL Search","netfind.aol.com","search");
		&search_words("AOL Search","netfind.aol.com/search.gw","s");
		&search_words("Metacrawler","metacrawler.com","general");
		&search_words("Infoseek","infoseek.com","qt");
		&search_words("AltaVista","altavista.digital.com","q");
		&search_words("AltaVista","altavista.com","q");
		&search_words("AltaVista","altavista.com","r");
		&search_words("AltaVista @ Telia.com","altavista.telia.com","q");
		&search_words("Search.Com","search.com","QUERY");
		&search_words("Yahoo","yahoo.com","p");
		&search_words("Yahoo (Non-USA)", "yahoo." , "p");
		&search_words("DogPile","dogpile.com","q");
		&search_words("HotBot","hotbot.com","MT");
		&search_words("Lycos","lycos.com","query");
		&search_words("Lycos","lycos.","query");
		&search_words("Webcrawler","webcrawler.com","searchText");
		&search_words("Webcrawler","webcrawler.com","search");
		&search_words("Inference Find","inference.com","query");
		&search_words("Anzwers","anzwers.ozemail.net","MT");
		&search_words("GoTo.com","goto.com","Keywords");
		&search_words("Highway 61","highway61.com","string");
		&search_words("Yellow Pages","altavista.yellowpages.com.au","q");
		&search_words("LookSmart","looksmart.com","key");
		&search_words("Snap","snap.com","keyword");
		&search_words("Ask Jeeves","askjeeves.com","ask");
		&search_words("Ask Jeeves","askjeeves.com","MetaTopic");
		&search_words("Excite at Netscape","excitesearch.netscape.com","search");
		&search_words("Excite at Netscape","excitesearch.netscape.com","s");
		&search_words("Developer.com","developer.com","search");
		&search_words("Magellan","mckinley.com","search");
		&search_words("1Blink","1blink.com","q");
		&search_words("Developer.com","developer.com","search");
		&search_words("Go2Net","go2net.com","general");
		&search_words("Go.com","go.com","qt");
		&search_words("MSN","msn.com","MT");
		&search_words("HotMail Email Message","hotmail.com","");
		&search_words("Ask Jeeves","ask.com","ask");
		&search_words("Excite (UK)","excite.co.uk","search");
#		&search_words("","","");
#		&search_words("","","");

		unless ($found) { 
			if ($from =~ /^http/) {
				$from = "<A HREF=\"$from\">$from</A>";
				}
			}
		}
	elsif ($from =~ /^http/) {
		$from = "<A HREF=\"$from\">$from</A>";
		}

	 $page = "<a href=\"$page\">" . $page ."</a>";

	# Modify based on content-type
	if ($page =~ /\.zip$/) { 
		$page = "<B>" . $page . "</B>";
		}
	if ($page =~ /\.jpg$/) {
		$page = "<font color=green>" . $page ."</font>";
		}

	if ( ($status !~ /^2/) && ($status !~ /^304/) ) {
		$status = "<font color=red>$status</font>";
		}

	print <<"END";
<TR>
<TD>$date</TD>
<TD>$page</TD>
<TD>$status</TD>
<TD>$from</TD>
</TR>
END
	}

    }
print "</TABLE>\n\n";

