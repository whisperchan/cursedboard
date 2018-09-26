#!/usr/bin/perl

use strict;
use warnings;
use Net::SFTP::SftpServer ( { log => 'local5' }, qw ( :LOG :ACTIONS ) );
use BSD::Resource;        # for setrlimit


my $MEMLIMIT = 50 * 1024 * 1024; # 50 Mb

# hard limits on process memory usage;
setrlimit( RLIMIT_RSS,  $MEMLIMIT, $MEMLIMIT );
setrlimit( RLIMIT_VMEM, $MEMLIMIT, $MEMLIMIT );

my $sftp = Net::SFTP::SftpServer->new(
  debug               => 0,
  home                => '/var/sftp/files',
  file_perms          => 0400,
  use_tmp_upload      => 0,
  max_file_size       => 10 * 1024 * 1024,
  valid_filename_char => [ 'a' .. 'z', 'A' .. 'Z', '0' .. '9', '_', '.', '-' ],
  deny                => ALL,
  allow               => [ (
                              SSH2_FXP_OPEN,
                              SSH2_FXP_CLOSE,
                              SSH2_FXP_READ,
                              SSH2_FXP_WRITE,
                              SSH2_FXP_LSTAT,
                              SSH2_FXP_STAT_VERSION_0,
                              SSH2_FXP_FSTAT,
                              SSH2_FXP_OPENDIR,
                              SSH2_FXP_READDIR,
                              SSH2_FXP_STAT,
                              SSH2_FXP_MKDIR,
                              SSH2_FXP_RMDIR,
                           )],
  fake_ok             => [ (
                              SSH2_FXP_SETSTAT,
                              SSH2_FXP_FSETSTAT,
                           )],
);

$sftp->run();
