#!/usr/bin/env python3
import typing
import pathlib
import subprocess
import sys, getopt

CONFS = [
    ("raspi", "bbb"),
]


def do_conf(cfg: typing.Tuple[str, str, str], tbotpath) -> None:
    # Find latest config
    logs = list(pathlib.Path("log").glob(f"{cfg[0]}-{cfg[1]}*.json"))
    logs.sort()
    log = logs[-1]
    junitdir = pathlib.Path("results/junit")
    junitdir.mkdir(exist_ok=True)
    junit_name = junitdir / f"{log.stem}.xml"
    print(f"{log} -> {junit_name}")
    handle = subprocess.Popen(
        [f"{tbotpath}/generators/junit.py", log], stdout=subprocess.PIPE
    )
    junit = handle.stdout.read().decode("utf-8")
    with open(junit_name, mode="w") as f:
        f.write(junit)

def main(argv) -> None:
    try:
        opts, args = getopt.getopt(argv,"hp:",["path="])
    except getopt.GetoptError:
        print('junit-logs.py -p <pathtotbot>')
        sys.exit(2)

    path = ''
    for opt, arg in opts:
        if opt == '-h':
            print('junit-logs.py -p <pathtotbot>')
            sys.exit()
        elif opt in ("-p", "--path"):
            path = arg

    for conf in CONFS:
        do_conf(conf, path)

if __name__ == "__main__":
    main(sys.argv[1:])
