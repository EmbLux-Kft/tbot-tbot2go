
RUNP=/home/hs/data/Entwicklung/wandboard/tbot-tbot2go
pwd
whoami
printenv PATH
PATH=/home/hs/.local/bin:$PATH
printenv PATH
cd $RUNP
pwd
source $RUNP/env_vars.sh

while :
do
	python3 timer.py -s 04 -m 00
	if [ $? -eq 0 ]
	then
		echo start with tbot test
		# maximal runtime 4 minutes!
		timeout -k 9 4.0m tbot @argswandboardlab1 wandboard_ub_build_install_test -q -q --log $TBOT_LOGFILE > $TBOT_STDIO_LOGFILE
		sync
		./push-testresult.py -p /home/hs/data/Entwicklung/tbot/ -f $TBOT_LOGFILE
		# wait one minute, so we trigger not again
		sleep 60
	fi
done
