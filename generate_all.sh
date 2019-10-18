#!/bin/sh

./dot-logs.py -p $1
./html-logs.py -p $1
./statistic-logs.py -p $1
./junit-logs.py -p $1
./ptest-logs.py -p $1
./iperf.sh
./latency.sh
#./create_doc-logs.py
