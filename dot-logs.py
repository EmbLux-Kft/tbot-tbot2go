#!/usr/bin/env python3
import typing
import pathlib
import subprocess
import os
import sys, getopt

CONFS = [
    ("smalllaptop", "wandboard"),
]

def do_conf(cfg: typing.Tuple[str, str, str], tbotpath) -> None:
    # Find latest config
    logs = list(pathlib.Path("log").glob(f"{cfg[0]}-{cfg[1]}*.json"))
    logs.sort()
    log = logs[-1]
    dotdir = pathlib.Path("results/dot")
    dotdir.mkdir(exist_ok=True)
    dot_name = dotdir / f"{log.stem}.dot"
    png_name = dotdir / f"{log.stem}.jpg"
    title = f"{log.stem}"
    print(f"{log} -> {dot_name}")
    handle = subprocess.Popen(
        [f"{tbotpath}/generators/dot.py", log], stdout=subprocess.PIPE
    )
    stats = handle.stdout.read().decode("utf-8")
    with open(dot_name, mode="w") as f:
        f.write(stats)

    cmd = "dot -Tjpg " + str(dot_name) + " > "  + str(png_name)
    os.system(cmd)

def main(argv) -> None:
    try:
        opts, args = getopt.getopt(argv,"hp:",["path="])
    except getopt.GetoptError:
        print('dot-logs.py -p <pathtotbot>')
        sys.exit(2)

    path = ''
    for opt, arg in opts:
        if opt == '-h':
            print('dot-logs.py -p <pathtotbot>')
            sys.exit()
        elif opt in ("-p", "--path"):
            path = arg

    for conf in CONFS:
        do_conf(conf, path)

if __name__ == "__main__":
    main(sys.argv[1:])
