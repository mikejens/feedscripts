#!/usr/bin/perl
use strict;
use warnings;
use Text::CSV_XS;
use Geo::StreetAddress::US;
use Getopt::Long;

my $csv = Text::CSV_XS->new();
my $header = ["id", "city", "zip", "street", "street_type", "house_number", "sec_unit_type", "sec_unit_number", "prefix", "precinct_code", "precinct_name"];

my $address;
my $hashref;
my $file;

my $result = GetOptions ("file=s"	=> \$file);
my $filewoextension = substr $file, 0, rindex $file, '.';

open (CSV_XS, "<", $file) or die $!;
open my $fh, ">", $filewoextension . "cleandata.txt" or die $filewoextension . "cleandata.txt: $!";
open my $errorfile, ">", $filewoextension . "cleandata.err" or die $filewoextension . "cleandata.err: $!";

$csv->print ($fh, $header);
print $fh "\n";

while (<CSV_XS>) {
	next if ($. == 1);
	if ($csv->parse($_)){
		my @columns = $csv->fields();
		$hashref = Geo::StreetAddress::US->parse_location($columns[10]) || { error => 'Could not geocode' };
		my $row = [$columns[0],$columns[12],$columns[14],$hashref->{street},$hashref->{type},$hashref->{number},$hashref->{sec_unit_type},$hashref->{sec_unit_number},$hashref->{prefix},$columns[38],$columns[37]];	
		$csv-> print ($fh, $row) or $csv->error_diag;	
		print $fh "\n";
	} else {
		my $err = $csv->error_input;
		print "Failed to parse line: $err";
		print $errorfile "$err" or $csv->error_diag;
	}
}
close CSV_XS;
close $fh or die $filewoextension . "cleandata.txt: $!";
close $errorfile or die $filewoextension . "cleandata.err: $!";
