#!/usr/bin/env python3

import argparse
from datetime import datetime
import json
import os
import schedule
import subprocess
import sys
import time


# pip3 install schedule --user
# https://schedule.readthedocs.io/en/stable/

def parse_arguments():
    parser = argparse.ArgumentParser(description='minimal CI')
    parser.add_argument(
            '-f',
            action='store_true',
            default=False,
            dest='force',
            help='force board build'
    )

    parser.add_argument(
            '-l',
            action='store_true',
            default=False,
            dest='list',
            help='list all boards'
    )

    parser.add_argument(
        "-n",
        dest="name",
        type=str,
        help="boardname for force",
    )

    parser.add_argument(
        "-c",
        dest="cfgfile",
        default='./minimal-ci.json',
        type=str,
        help="cfgfile",
    )


    args = parser.parse_args()
    return args

def parse_config(filename):
    with open(filename) as f:
        cfg = json.load(f)

    return cfg

def test_one_board(cfg, name):
    with_autocommit = False
    print(f'Test board {name}')
    tests = cfg["tests"]
    test = None
    for t in tests:
        if t["name"] == name:
            test = t
            break
    if test == None:
        print(f'board {name} not found in config.')
        sys.exit(1)

    # cfg -> Envvariables
    # test -> Testparameter
    print("Test ", test)
    tbotlog = cfg["TBOT_LOGFILE"].format(boarddir=name)
    tbotoutput = cfg["TBOT_STDIO_LOGFILE"].format(boarddir=name)
    systemmap = cfg["TBOT_SYSTEMMAP"].format(boarddir=name)
    print("tbotlog ", tbotlog)
    print("tbotout ", tbotoutput)
    print("systemmap ", systemmap)
    try:
        print("Path to DB ", cfg["DB_PATH"])
        with_autocommit = True
    except:
        pass

    path = os.path.dirname(tbotlog)
    print("PATH ", path)

    # start subshell

    bash = subprocess.Popen(["bash"],
                        stdin =subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        bufsize=0)

    # Send ssh commands to stdin
    bash.stdin.write("uname -a\n")
    bash.stdin.write(f'export SERVER_PORT={cfg["SERVER_PORT"]}\n')
    bash.stdin.write(f'export SERVER_URL={cfg["SERVER_URL"]}\n')
    bash.stdin.write(f'export SERVER_USER={cfg["SERVER_USER"]}\n')
    bash.stdin.write(f'export SERVER_PASSWORD={cfg["SERVER_PASSWORD"]}\n')
    bash.stdin.write(f'export TBOT_STDIO_LOGFILE={tbotoutput}\n')
    bash.stdin.write(f'export TBOT_LOGFILE={tbotlog}\n')
    bash.stdin.write(f'export TBOT_SYSTEMMAP={systemmap}\n')
    bash.stdin.write(f'export DB_PATH={cfg["DB_PATH"]}\n')

    bash.stdin.write("echo $TBOT_LOGFILE\n")
    bash.stdin.write("echo $TBOT_SYSTEMMAP\n")
    bash.stdin.write("echo $SERVER_PORT\n")
    # delete and create tmp result path
    bash.stdin.write(f'rm {path}/*\n')
    bash.stdin.write(f'mkdir -p {path}\n')
    bash.stdin.write(f'timeout -k 9 {test["timeout"]} tbot {test["tbotargs"]} {test["tbottest"]} --log {tbotlog} | tee {tbotoutput}\n')
    bash.stdin.write(f'sync\n')
    # copy tbot output into tbotoutput
    # ToDo do this in tbot with shell_copy
    bash.stdin.write(f'scp {test["systemmappath"]} {systemmap}\n')
    # push result to server
    bash.stdin.write(f'./push-testresult.py -p {cfg["TBOTPATH"]} -f {tbotlog}\n')
    bash.stdin.write(f'cat results/pushresults/tbot.txt\n')
    if with_autocommit:
        # commit DB changes in git
        bash.stdin.write(f'cd $DB_PATH\n')
        bash.stdin.write(f'git add .\n')
        at = datetime.utcnow()
        bash.stdin.write(f'git commit -m "site.db {name} {at}"\n')
    bash.stdin.close()
    for line in bash.stdout:
        print(line)


def main() -> None:  # noqa: C901
    args = parse_arguments()

    # parse cfg file
    cfg = parse_config(args.cfgfile)

    if args.list:
        print("Boards :")
        tests = cfg["tests"]
        for t in tests:
            print(t["name"])
        sys.exit(0)

    if args.force:
        print(f'Force testing board {args.name}')
        test_one_board(cfg, args.name)
        sys.exit(0)

    # schedule
    tests = cfg["tests"]
    for t in tests:
        print(f'Schedule {t["name"]} @ {t["starttime"]}')
        schedule.every().day.at(t["starttime"]).do(test_one_board, cfg=cfg, name=t["name"])

    while 1:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
