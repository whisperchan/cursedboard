#!/bin/bash

CURSEDBOARD_PY=/home/user/cursedboard/cursedboard.py

if [[ $1  == "-c" && $2 == "/var/sftp/sftp-server.pl" ]] ; then
	/var/sftp/sftp-server.pl

else
	shift
	$CURSEDBOARD_PY "$@"
fi
