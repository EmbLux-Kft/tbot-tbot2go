#!/usr/bin/env python3

import os
import subprocess
import sys

print ('Number of arguments:', len(sys.argv))
print ('Argument List:', str(sys.argv))

if len(sys.argv) < 2:
	sys.exit(-1)

jenkins_workspace = sys.argv[1]

# generate junit file
res = subprocess.run(["./junit-logs.py"], stdout=subprocess.PIPE)
result = str(res.stdout.decode('utf-8'))
fn = result.split("->")
json_fn = fn[0].strip()
fn = fn[1].strip()
res = subprocess.run(["cp", fn, jenkins_workspace + "/tbot_results.xml"], stdout=subprocess.PIPE)

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

# generate dot
res = subprocess.run(["./dot-logs.py"], stdout=subprocess.PIPE)
result = str(res.stdout.decode('utf-8'))
fn = result.split("->")
fn = fn[1].strip()
res = subprocess.run(["cp", fn, jenkins_workspace_tbot], stdout=subprocess.PIPE)
res = subprocess.run(["cp", fn.replace(".dot", ".jpg"), jenkins_workspace_tbot + "/graph.jpg"], stdout=subprocess.PIPE)

# generate html logs
res = subprocess.run(["./html-logs.py"], stdout=subprocess.PIPE)
result = str(res.stdout.decode('utf-8'))
fn = result.split("->")
fn = fn[1].strip()
res = subprocess.run(["cp", fn, jenkins_workspace_tbot], stdout=subprocess.PIPE)
res = subprocess.run(["cp", "results/html/myscript.js", jenkins_workspace_tbot], stdout=subprocess.PIPE)

# generate statistic
res = subprocess.run(["./statistic-logs.py"], stdout=subprocess.PIPE)
result = str(res.stdout.decode('utf-8'))
fn = result.split("->")
fn = fn[1].strip()
res = subprocess.run(["cp", fn, jenkins_workspace_tbot], stdout=subprocess.PIPE)
res = subprocess.run(["cp", fn.replace("txt", "jpg"), jenkins_workspace_tbot + "/statistic.jpg"], stdout=subprocess.PIPE)

# generate html
res = subprocess.run(["./create_doc-logs.py"], stdout=subprocess.PIPE)
result = str(res.stdout.decode('utf-8'))
fn = result.split("\n")
fn = fn[0].split("->")
fn = fn[1].strip()
res = subprocess.run(["cp", fn, jenkins_workspace_tbot], stdout=subprocess.PIPE)
res = subprocess.run(["cp", fn.replace("rst", "pdf"), jenkins_workspace_tbot + "/index.pdf"], stdout=subprocess.PIPE)

# collect other result files

# test results from U-Boot test/py
sname = json_fn.replace("json", "json-testpy-result.html")
cmd = "sed -i 's/<script src=\"http:\/\/code.jquery.com\/jquery.min.js\"><\/script>/<script src=\"myscript.js\"><\/script>/' " + sname
os.system(cmd)
res = subprocess.run(["cp", sname, f"{jenkins_workspace_tbot}/testpy.html"], stdout=subprocess.PIPE)

sname = json_fn.replace("json", "json-multiplexed_log.css")
res = subprocess.run(["cp", sname, f"{jenkins_workspace_tbot}/multiplexed_log.css"], stdout=subprocess.PIPE)
