#!/usr/bin/env python3

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
fn = fn[1].strip()
res = subprocess.run(["cp", fn, jenkins_workspace + "/tbot_results.xml"], stdout=subprocess.PIPE)

# setup subdir for tbot results
classname = "00 - piinstall_install_tools.00000 - piinstall_install_tools"
jenkins_workspace_tbot = jenkins_workspace + "/" + classname
res = subprocess.run(["mkdir", jenkins_workspace_tbot], stdout=subprocess.PIPE)

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
