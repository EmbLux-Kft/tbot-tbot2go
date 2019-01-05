#!/usr/bin/env python3
import typing
import pathlib
import subprocess
import os
import sys, getopt

CONFS = [
    ("smalllaptop", "wandboard", "./generators/create_doc_test"),
]

def do_conf(cfg: typing.Tuple[str, str, str], tbotpath) -> None:
    # Find latest config
    logs = list(pathlib.Path("log").glob(f"{cfg[0]}-{cfg[1]}-*.json"))
    logs.sort()
    log = logs[-1]
    docdir = pathlib.Path("results/doc")
    docdir.mkdir(exist_ok=True)
    doc_name = docdir / f"{log.stem}.rst"
    pdf_name = docdir / f"{log.stem}.pdf"
    rst_p = f"{cfg[2]}"
    title = f"{log.stem}"
    print(f"{log} -> {doc_name}")
    print(f"{log} -> {pdf_name}")
    handle = subprocess.Popen(
        [f"{tbotpath}/generators/create_doc.py", log, rst_p], stdout=subprocess.PIPE
    )
    stats = handle.stdout.read().decode("utf-8")
    with open(doc_name, mode="w") as f:
        f.write(stats)

    cmd = "rst2pdf -s " + str(rst_p) + "/stylesheet.txt" + " " + str(doc_name) + " " + str(pdf_name)
    os.system(cmd)

def main(argv) -> None:
    try:
        opts, args = getopt.getopt(argv,"hp:",["path="])
    except getopt.GetoptError:
        print('create_doc-logs.py -p <pathtotbot>')
        sys.exit(2)

    path = ''
    for opt, arg in opts:
        if opt == '-h':
            print('create_doc-logs.py -p <pathtotbot>')
            sys.exit()
        elif opt in ("-p", "--path"):
            path = arg

    for conf in CONFS:
        do_conf(conf, path)

if __name__ == "__main__":
    main(sys.argv[1:])
