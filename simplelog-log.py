#!/usr/bin/env python3
import typing
import pathlib
import subprocess
import sys, getopt

CONFS = [
    ("raspi", "k30rf"),
]


def do_conf(cfg: typing.Tuple[str, str, str], tbotpath, ubmachinename, fn) -> None:
    if fn == '':
        # Find latest config
        logs = list(pathlib.Path("log").glob(f"{cfg[0]}-{cfg[1]}*.json"))
        logs.sort()
        log = logs[-1]
    else:
        if fn[0] == '/':
            logs = list(pathlib.Path("/").glob(fn[1:]))
        else:
            logs = list(pathlib.Path("").glob(fn))
        if len(logs) == 0:
            print(f"logfile {fn} not found")
            sys.exit(2)
        log = logs[0]

    logdir = pathlib.Path("results/simplelog")
    logdir.mkdir(exist_ok=True)
    log_name = logdir / f"{log.stem}.txt"
    print(f"{log} -> {log_name}")
    handle = subprocess.Popen(
        [f"{tbotpath}/generators/simplelog.py", log, ubmachinename], stdout=subprocess.PIPE
    )
    hf = handle.stdout.read().decode("utf-8")
    with open(log_name, mode="w") as f:
        f.write(hf)

def main(argv) -> None:
    try:
        opts, args = getopt.getopt(argv,"hp:u:t:",["path=", "ub=", "fn="])
    except getopt.GetoptError:
        print('simplelog-logs.py -p <pathtotbot> -u <u-boot machine name> -f <tbot logfilename>')
        sys.exit(2)

    path = ''
    ub = 'unknown'
    fn = ''
    for opt, arg in opts:
        if opt == '-h':
            print('simplelog-logs.py -p <pathtotbot> -u <u-boot machine name> -f <tbot logfilename>')
            sys.exit()
        elif opt in ("-p", "--path"):
            path = arg
        elif opt in ("-u", "--ubootmachine"):
            ub = arg
        elif opt in ("-f", "--file"):
            fn = arg

    for conf in CONFS:
        do_conf(conf, path, ub, fn)

if __name__ == "__main__":
    main(sys.argv[1:])
