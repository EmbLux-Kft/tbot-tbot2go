#!/usr/bin/env python3
import typing
import pathlib
import subprocess
import os

CONFS = [
    ("pollux", "bbb"),
    ("pollux", "corvus"),
    ("pollux", "fipad-b3"),
    ("pollux", "pxc5"),
    ("pollux", "lcd5c-a"),
]


def do_conf(cfg: typing.Tuple[str, str]) -> None:
    # Find latest config
    logs = list(pathlib.Path("log").glob(f"{cfg[0]}-{cfg[1]}-*.json"))
    logs.sort()
    log = logs[-1]
    htmldir = pathlib.Path("results/html")
    htmldir.mkdir(exist_ok=True)
    html_name = htmldir / f"{log.stem}.html"
    print(f"{log} -> {html_name}")
    handle = subprocess.Popen(
        ["../tbot/generators/htmllog.py", log], stdout=subprocess.PIPE
    )
    html = handle.stdout.read().decode("utf-8")
    with open(html_name, mode="w") as f:
        f.write(html)

    # use private script
    cmd = "sed -i 's/<script src=\"http:\/\/code.jquery.com\/jquery.min.js\"><\/script>/<script src=\"myscript.js\"><\/script>/' " + str(html_name)
    os.system(cmd)
def main() -> None:
    for conf in CONFS:
        do_conf(conf)


if __name__ == "__main__":
    main()
