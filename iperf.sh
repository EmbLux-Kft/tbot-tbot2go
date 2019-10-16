#!/bin/sh

if [ -f "results/iperf/iperf.dat" ]
then
    gnuplot -e 'output_file="results/iperf/iperf.jpg";input_file="results/iperf/iperf.dat";graph_title="iperf"' results/iperf/balkenplot_iperf.sem
    scp results/iperf/iperf.jpg hs@192.168.1.106:/home/hs/data/Entwicklung/bbb/src
fi
