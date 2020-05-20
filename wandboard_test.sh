FORCE=0
RUNP=/home/hs/data/Entwicklung/wandboard/tbot-tbot2go

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -f|--force)
    FORCE=1
    shift # past argument
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done

echo FORCE $FORCE
cd $RUNP
pwd
source $RUNP/env_vars.sh
export TBOT_SYSTEMMAP="/var/lib/tftpboot/wandboard/tbot/System.map"
echo "JSON " $TBOT_LOGFILE
echo "LOG  " $TBOT_STDIO_LOGFILE
echo "SYSTEM MAP  " $TBOT_SYSTEMMAP

while :
do
	if [ $FORCE -eq 0 ];then
		python3 timer.py -s 04 -m 00
	else
		echo "forced run"
	fi
	if [ $? -eq 0 ]
	then
		echo start with tbot test
		if [ $FORCE -eq 0 ];then
			# maximal runtime 4 minutes!
			timeout -k 9 4.0m tbot @argswandboardlab1 wandboard_ub_build_install_test -q -q --log $TBOT_LOGFILE | tee $TBOT_STDIO_LOGFILE
			sync
			./push-testresult.py -p /home/hs/data/Entwicklung/tbot/ -f $TBOT_LOGFILE
			# wait one minute, so we trigger not again
			sleep 60
		else
			tbot @argswandboardlab1 wandboard_ub_build_install_test --log $TBOT_LOGFILE | tee $TBOT_STDIO_LOGFILE
			sync
			./push-testresult.py -p /home/hs/data/Entwicklung/tbot/ -f $TBOT_LOGFILE
			exit 0
		fi
	fi
done
