#!/usr/bin/env python3
import typing
import pathlib
import subprocess
import os

CONFS = [
    ("raspi", "bbb"),
]

def do_conf(cfg: typing.Tuple[str, str, str]) -> None:
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
        ["/home/hs/data/Entwicklung/newtbot/tbot/generators/dot.py", log], stdout=subprocess.PIPE
    )
    stats = handle.stdout.read().decode("utf-8")
    with open(dot_name, mode="w") as f:
        f.write(stats)

    cmd = "dot -Tjpg " + str(dot_name) + " > "  + str(png_name)
    os.system(cmd)

def main() -> None:
    for conf in CONFS:
        do_conf(conf)

if __name__ == "__main__":
    main()
