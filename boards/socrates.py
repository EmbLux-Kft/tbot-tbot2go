import typing
import tbot
from tbot.machine import board, channel, linux, connector

if tbot.selectable.LabHost.name == "pollux":
    # Use pollux specific config
    import denx as lab
else:
    raise NotImplementedError("Board not available on this labhost!")

class socrates(lab.Board):
    name = "socrates"
    connect_wait = 2.0
    date = "20200508"
    envdir = f"socrates-abb/{date}/env.txt"

class socratesUBoot(lab.UBootMachine):
    name = "soc-ub"
    prompt = "=> "
    autoboot_prompt = None

BOARD = socrates
UBOOT = socratesUBoot
