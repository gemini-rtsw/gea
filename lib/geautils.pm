package geautils;

use Getopt::Std;
use Cwd;
use archiveconfig;
use base Exporter;
our @EXPORT = qw(run);
our @EXPORT_OK = qw($config $gea_base $gea_conf $gea_data $gea_root $gea_host $doall $nope $debug);

our $gea_base = $ENV{'GEA_BASE'};
our $gea_conf = $ENV{'GEA_CONF'};
our $gea_data = $ENV{'GEA_DATA'};
our $gea_host = $ENV{'GEA_HOST'};
our $gea_root;				# Contents of, "<root>xxx</root> tag in archiveconfig.xml. OPTIONAL!
our $doall;				# Passed in behavior doall, such as always do all engines.
our $nope = 0;	 			# Don't actually do anything flag passed to caller.
our $debug = 0;	 			# Debug messages.
our $doall = 0;	 			# Do all engines flag.
our $config;

use vars qw($opt_n $opt_a $opt_d $opt_h $opt_c);

#
# Call callbacks for each daemon and engine as encountered in archiveconfig.xml.
# Behavior can be modified by command line options;
#    -d Debug
#    -a All engines
#    -h Help
#    <argument> Only for specific engine, error otherwise
#    No arguments, pick last name in pathname.
#

sub run
{
    my $opts .= "andhc:";
    if (!getopts($opts) ||  $opt_h) {
        print "Bad options\n";
        exit(0);
    }

    $nope  = $opt_n;
    $debug = $opt_d;
    $doall = 1 if $opt_a;	# Note that our caller also could have set doall.

    if (! $doall) {
        # Try to get engine name to do. Could be command line argument, or last part of pathname.
        if ($ARGV[0]) {
            $do_engine = $ARGV[0];
            $doall = 1 if ($do_engine eq "all");
        }
        else {
            $do_engine = cwd();
            $do_engine =~ s/^.*\///;
        }
    }

    if ($opt_d) {
        print "All engines\n" if $doall;
        print "Just do engine $do_engine\n" unless $doall;
        print "Debug enabled\n" if $opt_d;
    }

    my ($d_subref, $e_subref) = @_;
    my $config_path;
    if ($opt_c) {
        $config_path .= $opt_c;
    }
    else {
        $config_path .= "$gea_conf/archiveconfig.xml";
    }

    print "Using archive config \"$config_path\"\n" if $opt_d;

    $config = parse_config_file($config_path, $opt_d);
    $gea_root = "/" . $config->{root} if defined($config->{root});
    $config->{configpath} = $config_path;

    my ($d_name, $e_name, $err);
    foreach $d_name ( sort keys %{ $config->{daemon} } )
    {
        &$d_subref($d_name);
        $err = 1;
        foreach $e_name ( sort keys %{ $config->{daemon}{$d_name}{engine} } )
        {
            if ($doall) {
                &$e_subref($d_name, $e_name);
                $err = 0;
            } elsif ($do_engine eq $e_name) {
                &$e_subref($d_name, $e_name);
                $err = 0;
            }
        }
        print "No such engine, \"$do_engine\"\n" if $err;
    }
}

1;
