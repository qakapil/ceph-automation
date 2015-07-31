#!/bin/bash
set -e

#--
runLibiSCSITests()
{
	 #-- 
        ISCSI_PROTOCOL="iscsi://"

        #-- Arguments passed.
        IP_ADDR=$1
        ISCSI_PORT=$2
        IQN_ADDR=$3

	#-- 
	#iscsi-test-cu -d -t ALL iscsi://10.160.223.10:3260/iqn.1996-04.de.suse:01:cd52c4d99b/
	iscsi-test-cu -d -t ALL ${ISCSI_PROTOCOL}${IP_ADDR}:${ISCSI_PORT}/${IQN_ADDR}/0
}

#--
main() 
{
	#--
	CURRENT_DIR=`dirname $0`
	LIBISCSI_NEEDED_UTIL="iscsi-test-cu"
	LIBISCSI_UTIL_INSTALLED=$(which $LIBISCSI_NEEDED_UTIL 2>/dev/null)

	if [ -x $LIBISCSI_UTIL_INSTALLED ]; then 
		runLibISCSITests "${1}" "${2}" "${3}" 
	else 
		echo "Could not find: ${LIBISCSI_NEEDED_UTIL} " 
	        echo "Aborting..." 
        	exit 2
	fi      #-- if [ -x $LIBISCSI_UTIL_INSTALLED ]
}
main $*
