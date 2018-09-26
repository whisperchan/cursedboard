#!/bin/bash

SFTP_SERVER="/var/sftp/sftp-server.pl"
CURSEDBOARD_PY=/home/bit/cursedboard/cursedboard.py

if [[ $1  == "-c" && $2 == $SFTP_SERVER ]] ; then
	$SFTP_SERVER
else
	shift
	$CURSEDBOARD_PY "$@"
fi
