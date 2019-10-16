#!/usr/bin/env python3

import os
import subprocess
import sys

print ('Number of arguments:', len(sys.argv))
print ('Argument List:', str(sys.argv))

if len(sys.argv) < 3:
	sys.exit(-1)

jenkins_workspace = sys.argv[1]
tbot_path = sys.argv[2]

name = "raspi-bbb"
wp = "/home/hs/src/bbb/tbot-tbot2go"
res_path = "results"

# generate junit file
res = subprocess.run([f"{wp}/generate_all.sh", tbot_path], stdout=subprocess.PIPE)
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

jenkins_workspace_tbot = jenkins_workspace + "/" + classname
res = subprocess.run(["mkdir", "-p", jenkins_workspace_tbot], stdout=subprocess.PIPE)

# cp dot results
subdirname = "dot"
tmpp = f"{res_path}/{subdirname}"

res = subprocess.run(["cp", f"{tmpp}/{name}.dot", f"{jenkins_workspace_tbot}"], stdout=subprocess.PIPE)
res = subprocess.run(["cp", f"{tmpp}/{name}.jpg", f"{jenkins_workspace_tbot}/graph.jpg"], stdout=subprocess.PIPE)

# cp html results
subdirname = "html"
tmpp = f"{res_path}/{subdirname}"
res = subprocess.run(["cp", f"{tmpp}/myscript.js", f"{jenkins_workspace_tbot}"], stdout=subprocess.PIPE)
res = subprocess.run(["cp", f"{tmpp}/{name}.html", f"{jenkins_workspace_tbot}"], stdout=subprocess.PIPE)

# cp statistic
subdirname = "stats"
tmpp = f"{res_path}/{subdirname}"
res = subprocess.run(["cp", f"{tmpp}/balkenplot.sem", f"{jenkins_workspace_tbot}"], stdout=subprocess.PIPE)
res = subprocess.run(["cp", f"{tmpp}/{name}.jpg", f"{jenkins_workspace_tbot}/statistic.jpg"], stdout=subprocess.PIPE)
res = subprocess.run(["cp", f"{tmpp}/{name}.txt", f"{jenkins_workspace_tbot}/statistic_data.txt"], stdout=subprocess.PIPE)

# cp ptest
subdirname = "ptest"
tmpp = f"{res_path}/{subdirname}"
res = subprocess.run(["cp", f"{tmpp}/{name}.jpg", f"{jenkins_workspace_tbot}/ptest.jpg"], stdout=subprocess.PIPE)
res = subprocess.run(["cp", f"{tmpp}/{name}.txt", f"{jenkins_workspace_tbot}/ptest_data.txt"], stdout=subprocess.PIPE)
res = subprocess.run(["cp", f"{tmpp}/balkenplot.sem", f"{jenkins_workspace_tbot}/balkenplot_ptest.sem"], stdout=subprocess.PIPE)
