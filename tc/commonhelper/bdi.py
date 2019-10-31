import contextlib
import typing
import shlex
import os
import time
import tbot
from tbot.machine import board, channel, linux, connector
import generic as ge

class Bdi:
    """class for bdi tasks

    cfg : configuration dictionary
    """

    def __init__(self, bdiname, prompt, thumbbase, loadaddrspl, loadaddrub, splfile, ubfile):
        self.bdiname = bdiname
        self.name = self.bdiname
        self.prompt = prompt
        self.thumbbase = thumbbase
        self.loadaddrspl = loadaddrspl
        self.loadaddrub = loadaddrub
        self.splfile = splfile
        self.ubfile = ubfile
        self.bdiend = '\r'
        self.wait = 0.5

    def build_command(
        self, *args: typing.Union[str]
    ) -> str:
        command = ""
        for arg in args:
            command += f"{shlex.quote(arg)} "

        return command[:-1]

    def exec(
        self,
        *args: typing.Union[str]
    ) -> str:
        command = self.build_command(*args)

        with tbot.log_event.command(self.name, command) as ev:
            ev.prefix = "   >> "

            self.lhbdi.send(command + self.bdiend)
            out = self.lhbdi.read_until_prompt(self.prompt, stream=ev)
            ev.data["stdout"] = out

        return out

    @tbot.testcase
    def check_ready(
        self,
    ) -> str:
        while (True):
            ret = self.exec("i")
            if "Current SPSR" in ret:
                return ret
            elif "running" in ret:
                self.bdi_reset_board()
            else:
                time.sleep(self.wait)

    @tbot.testcase
    def bdi_go2arm(
        self,
    ) -> str:
        ret = self.check_ready()
        if 'THUMB' not in ret:
            return None

        self.exec("MM", self.thumbbase, "0x4700a000")
        self.exec("ti", self.thumbbase)
        self.exec("t")
        while (True):
            ret = self.check_ready()
            if 'THUMB' not in ret:
                return None
            self.exec("t")

    @tbot.testcase
    def bdi_connect(
        self,
        lh: typing.Optional[linux.Lab],
        b: typing.Optional[board.Board],
    ) -> None:
        self.lhbdi = lh.new_channel("telnet", self.bdiname)
        self.lhbdi.read_until_prompt(self.prompt)
        self.check_ready()

    @tbot.testcase
    def bdi_reset_board(
        self,
    ) -> None:
        ret = self.exec("res", "halt")
        self.check_ready()

    @tbot.testcase
    def bdi_load_spl(
        self,
    ) -> None:
        self.exec("load", self.loadaddrspl, self.splfile, "BIN")
        self.exec("t", self.loadaddrspl)
        self.exec("ci")
        self.exec("bi", self.loadaddrub)
        self.exec("g")

        # check if bdi stops
        raw = b""
        try:
            loop = True
            while loop:
                raw += self.lhbdi.recv_n(1, timeout=2.0)
        except TimeoutError:
            pass

        if "has entered debug mode" not in str(raw):
            raise RuntimeError("Could not stop on breakpoint " + self.loadaddrub)

    @tbot.testcase
    def bdi_load_ub(
        self,
    ) -> None:
        self.exec("load", self.loadaddrub, self.ubfile, "BIN")
        self.exec("t", self.loadaddrub)
        self.exec("g")
