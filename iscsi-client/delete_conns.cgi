#!/usr/local/bin/perl
# Remove one or more active connections

use strict;
use warnings;
require './iscsi-client-lib.pl';
our (%text, %in);
&ReadParse();
&error_setup($text{'dconns_err'});

# Get the connections
my $conns = &list_iscsi_connections();
ref($conns) || &error(&text('conns_elist', $conns));
my @d = split(/\0/, $in{'d'});
my @delconns;
foreach my $d (@d) {
	my ($conn) = grep { $_->{'num'} eq $d } @$conns;
	push(@delconns, $conn) if ($conn);
	}
@delconns || &error($text{'dconns_enone'});

if (!$in{'confirm'}) {
	&ui_print_header(undef, $text{'dconns_title'}, "");

	# Find users of each device
	my @users;
	my @disks = &fdisk::list_disks_partitions();
	foreach my $conn (@delconns) {
		next if (!$conn->{'device'});
		my ($disk) = grep { $_->{'device'} eq $conn->{'device'} }
				  @disks;
		next if (!$disk);
		foreach my $part (@{$disk->{'parts'}}) {
			my @st = &fdisk::device_status($part->{'device'});
			if (@st) {
				push(@users, [ $conn, $part->{'device'}, @st ]);
				}
			}
		}

	# Build table of users
	my $utable = "";
	if (@users) {
		$utable = $text{'dconns_users'}."<p>\n";
		$utable .= &ui_columns_start([
			$text{'conns_ip'},
			$text{'conns_target'},
			$text{'dconns_part'},
			$text{'dconns_use'} ]);
		foreach my $u (@users) {
			$utable .= &ui_columns_row([
				$u->[0]->{'ip'},
				$u->[0]->{'target'},
				&mount::device_name($u->[1]),
				&lvm::device_message($u->[2], $u->[3], $u->[4]),
				], "50");
			}
		$utable .= &ui_columns_end();
		}

	# Ask the user if he is sure
	print &ui_confirmation_form(
		"delete_conns.cgi",
		&text('dconns_rusure', scalar(@delconns)),
		[ map { [ "d", $_ ] } @d ],
		[ [ "confirm", $text{'dconns_confirm'} ] ],
		$utable);

	&ui_print_footer("", $text{'index_return'});
	}
else {
	# Delete each one
	foreach my $conn (@delconns) {
		my $err = &delete_iscsi_connection($conn);
		&error(&text('dconns_edelete', $conn->{'ip'},
			     $conn->{'target'}, $err)) if ($err);
		}

	&webmin_log("delete", "connection", scalar(@delconns));
	&redirect("list_conns.cgi");
	}