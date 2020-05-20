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
source $RUNP/env_vars.sh
export TBOT_SYSTEMMAP="/tmp/System.map"

echo TBOT STDIO LOG: $TBOT_STDIO_LOGFILE
echo TBOT JSON  LOG: $TBOT_LOGFILE
echo "SYSTEM MAP  " $TBOT_SYSTEMMAP

while :
do
	if [ $FORCE -eq 0 ];then
		python3 timer.py -s 10 -m 00
	else
		echo "forced run"
	fi
	if [ $? -eq 0 ]
	then
		echo start with tbot test
		if [ $FORCE -eq 0 ];then
			# maximal runtime 4 minutes!
			timeout -k 9 4.0m tbot @argssocrates socrates_ub_build_install_test -q -q --log $TBOT_LOGFILE | tee $TBOT_STDIO_LOGFILE
			sync
			scp pollux.denx.org:/tftpboot/socrates-abb/20200508/System.map /tmp
			./push-testresult.py -p /home/hs/data/Entwicklung/tbot/ -f $TBOT_LOGFILE
			# wait one minute, so we trigger not again
			sleep 60
		else
			tbot @argssocrates socrates_ub_build_install_test --log $TBOT_LOGFILE | tee $TBOT_STDIO_LOGFILE
			sync
			scp pollux.denx.org:/tftpboot/socrates-abb/20200508/System.map /tmp
			./push-testresult.py -p /home/hs/data/Entwicklung/tbot/ -f $TBOT_LOGFILE
			exit 0
		fi
	fi
done
