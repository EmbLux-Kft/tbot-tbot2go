#!/usr/bin/env python3

import os
import subprocess
import sys
import pathlib

print ('Number of arguments:', len(sys.argv))
print ('Argument List:', str(sys.argv))

if len(sys.argv) < 3:
	sys.exit(-1)

jenkins_workspace = sys.argv[1]
tbot_path = sys.argv[2]

prename = "raspi-bbb"
wp = "/home/hs/src/bbb/tbot-tbot2go"
res_path = "results"

# generate junit file
res = subprocess.run([f"{wp}/generate_all.sh", tbot_path], stdout=subprocess.PIPE)
# get log number
logs = list(pathlib.Path("results/junit").glob(f"{prename}-*.xml"))
logs.sort()
log = logs[-1]
log = str(log)
number = log.split("-")[2]
number = number.split(".")[0]
name = f"{prename}-{number}"
res = subprocess.run(["cp", f"results/junit/{name}.xml", jenkins_workspace + "/tbot_results.xml"], stdout=subprocess.PIPE)

# setup subdir for tbot results
classname = ""
with open(jenkins_workspace + "/tbot_results.xml", "r") as f:
    for line in f:
        if "classname=" in line:
            line = line.split('"')
            classname = line[1]
            break

if classname == "":
    print("Could not detect classname")
    sys.exit(-1)

classname = "tbot_results"
jenkins_workspace_tbot = jenkins_workspace + "/" + classname
res = subprocess.run(["mkdir", "-p", jenkins_workspace_tbot], stdout=subprocess.PIPE)

# cp dot results
subdirname = "dot"
tmpp = f"{res_path}/{subdirname}"
res = subprocess.run(["test", "-f", f"{tmpp}/{name}.jpg"], stdout=subprocess.PIPE)
if res.returncode == 0:
    res = subprocess.run(["cp", f"{tmpp}/{name}.dot", f"{jenkins_workspace_tbot}"], stdout=subprocess.PIPE)
    res = subprocess.run(["cp", f"{tmpp}/{name}.jpg", f"{jenkins_workspace_tbot}/graph.jpg"], stdout=subprocess.PIPE)

# cp html results
subdirname = "html"
tmpp = f"{res_path}/{subdirname}"
res = subprocess.run(["test", "-f", f"{tmpp}/{name}.html"], stdout=subprocess.PIPE)
if res.returncode == 0:
    res = subprocess.run(["cp", f"{tmpp}/myscript.js", f"{jenkins_workspace_tbot}"], stdout=subprocess.PIPE)
    res = subprocess.run(["cp", f"{tmpp}/{name}.html", f"{jenkins_workspace_tbot}"], stdout=subprocess.PIPE)

# cp statistic
subdirname = "stats"
tmpp = f"{res_path}/{subdirname}"
res = subprocess.run(["test", "-f", f"{tmpp}/{name}.jpg"], stdout=subprocess.PIPE)
if res.returncode == 0:
    res = subprocess.run(["cp", f"{tmpp}/balkenplot.sem", f"{jenkins_workspace_tbot}"], stdout=subprocess.PIPE)
    res = subprocess.run(["cp", f"{tmpp}/{name}.jpg", f"{jenkins_workspace_tbot}/statistic.jpg"], stdout=subprocess.PIPE)
    res = subprocess.run(["cp", f"{tmpp}/{name}.txt", f"{jenkins_workspace_tbot}/statistic_data.txt"], stdout=subprocess.PIPE)

# cp ptest
subdirname = "ptest"
tmpp = f"{res_path}/{subdirname}"
res = subprocess.run(["test", "-f", f"{tmpp}/{name}.jpg"], stdout=subprocess.PIPE)
if res.returncode == 0:
    res = subprocess.run(["cp", f"{tmpp}/{name}.jpg", f"{jenkins_workspace_tbot}/ptest.jpg"], stdout=subprocess.PIPE)
    res = subprocess.run(["cp", f"{tmpp}/{name}.txt", f"{jenkins_workspace_tbot}/ptest_data.txt"], stdout=subprocess.PIPE)
    res = subprocess.run(["cp", f"{tmpp}/balkenplot.sem", f"{jenkins_workspace_tbot}/balkenplot_ptest.sem"], stdout=subprocess.PIPE)

# iperf ptest
subdirname = "iperf"
tmpp = f"{res_path}/{subdirname}"
res = subprocess.run(["test", "-f", f"{tmpp}/iperf.jpg"], stdout=subprocess.PIPE)
if res.returncode == 0:
    res = subprocess.run(["cp", f"{tmpp}/iperf.jpg", f"{jenkins_workspace_tbot}/iperf.jpg"], stdout=subprocess.PIPE)
    res = subprocess.run(["cp", f"{tmpp}/iperf.dat", f"{jenkins_workspace_tbot}/iperf_data.txt"], stdout=subprocess.PIPE)
    res = subprocess.run(["cp", f"{tmpp}/balkenplot_iperf.sem", f"{jenkins_workspace_tbot}/balkenplot_iperf.sem"], stdout=subprocess.PIPE)

# latency ptest
subdirname = "latency"
tmpp = f"{res_path}/{subdirname}"
res = subprocess.run(["test", "-f", f"{tmpp}/latency.jpg"], stdout=subprocess.PIPE)
if res.returncode == 0:
    res = subprocess.run(["cp", f"{tmpp}/latency.jpg", f"{jenkins_workspace_tbot}/latency.jpg"], stdout=subprocess.PIPE)
    res = subprocess.run(["cp", f"{tmpp}/latency.dat", f"{jenkins_workspace_tbot}/latency_data.txt"], stdout=subprocess.PIPE)
    res = subprocess.run(["cp", f"{tmpp}/balkenplot.sem", f"{jenkins_workspace_tbot}/balkenplot_latency.sem"], stdout=subprocess.PIPE)
