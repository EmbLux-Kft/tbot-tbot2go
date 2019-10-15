#!/usr/bin/env python3
import typing
import pathlib
import subprocess

CONFS = [
    ("raspi", "bbb"),
]


def do_conf(cfg: typing.Tuple[str, str]) -> None:
    # Find latest config
    logs = list(pathlib.Path("log").glob(f"{cfg[0]}-{cfg[1]}*.json"))
    logs.sort()
    log = logs[-1]
    junitdir = pathlib.Path("results/junit")
    junitdir.mkdir(exist_ok=True)
    junit_name = junitdir / f"{log.stem}.xml"
    print(f"{log} -> {junit_name}")
    handle = subprocess.Popen(
        ["/home/hs/data/Entwicklung/newtbot/tbot/generators/junit.py", log], stdout=subprocess.PIPE
    )
    junit = handle.stdout.read().decode("utf-8")
    with open(junit_name, mode="w") as f:
        f.write(junit)


def main() -> None:
    for conf in CONFS:
        do_conf(conf)

if __name__ == "__main__":
    main()
