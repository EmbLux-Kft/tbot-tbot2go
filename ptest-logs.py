#!/usr/bin/env python3
import typing
import pathlib
import subprocess
import os
import sys, getopt

# good examples for balkenplot.sem
# http://gnuplot.sourceforge.net/demo/histograms.html

CONFS = [
    ("raspi", "bbb", "results/ptest/balkenplot.sem"),
]

def do_conf(cfg: typing.Tuple[str, str], tbotpath) -> None:
    # Find latest config
    logs = list(pathlib.Path("log").glob(f"{cfg[0]}-{cfg[1]}*.json"))
    logs.sort()
    log = logs[-1]
    ptestdir = pathlib.Path("results/ptest")
    ptestdir.mkdir(exist_ok=True)
    stat_name = ptestdir / f"{log.stem}.txt"
    jpg_name = ptestdir / f"{log.stem}.jpg"
    title = f"{log.stem}"
    print(f"{log} -> {stat_name}")
    handle = subprocess.Popen(
        [f"{tbotpath}/generators/ptest-runner.py", log], stdout=subprocess.PIPE
    )
    stats = handle.stdout.read().decode("utf-8")
    with open(stat_name, mode="w") as f:
        f.write(stats)

    cmd = 'gnuplot -e \'output_file="'+ str(jpg_name) + '";input_file="' + str(stat_name) + '";graph_title="' + title + '"\' ' + cfg[2]
    os.system(cmd)

def main(argv) -> None:
    try:
        opts, args = getopt.getopt(argv,"hp:",["path="])
    except getopt.GetoptError:
        print('ptest-runner.py -p <pathtotbot>')
        sys.exit(2)

    path = ''
    for opt, arg in opts:
        if opt == '-h':
            print('ptest-runner.py -p <pathtotbot>')
            sys.exit()
        elif opt in ("-p", "--path"):
            path = arg

    for conf in CONFS:
        do_conf(conf, path)

if __name__ == "__main__":
    main(sys.argv[1:])
