#!/usr/bin/env python3
import typing
import pathlib
import subprocess
import os

CONFS = [
    ("raspi", "k30rf", "results/stats/balkenplot.sem"),
]

def do_conf(cfg: typing.Tuple[str, str, str]) -> None:
    # Find latest config
    logs = list(pathlib.Path("log").glob(f"{cfg[0]}-{cfg[1]}-*.json"))
    logs.sort()
    log = logs[-1]
    #log = pathlib.Path("log/raspi-h03pl086-0042.json")
    statdir = pathlib.Path("results/stats")
    statdir.mkdir(exist_ok=True)
    stat_name = statdir / f"{log.stem}.txt"
    jpg_name = statdir / f"{log.stem}.jpg"
    title = f"{log.stem}"
    print(f"{log} -> {stat_name}")
    handle = subprocess.Popen(
        ["generators/statistic.py", log], stdout=subprocess.PIPE
    )
    stats = handle.stdout.read().decode("utf-8")
    with open(stat_name, mode="w") as f:
        f.write(stats)

    cmd = 'gnuplot -e \'output_file="'+ str(jpg_name) + '";input_file="' + str(stat_name) + '";graph_title="' + title + '"\' ' + cfg[2]
    os.system(cmd)

def main() -> None:
    for conf in CONFS:
        do_conf(conf)

if __name__ == "__main__":
    main()
