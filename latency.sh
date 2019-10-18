#!/bin/sh

if [ -f "results/latency/latency.dat" ]
then
    gnuplot -e 'output_file="results/latency/latency.jpg";input_file="results/latency/latency.dat";graph_title="Test mode: periodic user-mode task"' results/latency/balkenplot.sem
    scp results/latency/latency.jpg hs@192.168.1.106:/home/hs/data/Entwicklung/bbb/src
fi
