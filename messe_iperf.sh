#!/usr/bin/env bash

WORKSPACE=$1
cycles=$2
status=0

echo "start"
whoami
pwd
echo ${WORKSPACE}
echo cycles $cycles

# switch to user hs
# this is an ugly hack, as jenkins randomly starts
# this script with user hs or jenkins !!!!
sudo su - hs << EOF
echo "In"
whoami
pwd
echo ${WORKSPACE}

export PATH=/home/hs/bin:/home/hs/.local/bin:$PATH
echo cycles $cycles

cd /home/hs/tbot-tbot2go
tbot @argswandboard -p cycles=\"$cycles\" wandboard_check_iperf
status=$?
echo "RETURN VALUE " $status
./generate_jenkins_result.py ${WORKSPACE} /home/hs/tbot

EOF
echo "Out"
whoami
echo "RETURN VALUE " $status
[ $status -ne 0 ] && exit 1
exit 0
