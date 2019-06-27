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

    def __init__(self, bdiname, prompt, thumbbase, loadaddrspl, loadaddrub, splfile, ubfile, bdicfgfile):
        self.bdiname = bdiname
        self.name = self.bdiname
        self.prompt = prompt
        self.thumbbase = thumbbase
        self.loadaddrspl = loadaddrspl
        self.loadaddrub = loadaddrub
        self.splfile = splfile
        self.ubfile = ubfile
        self.bdicfgfile = bdicfgfile
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
        check_run = True,
    ) -> str:
        while (True):
            ret = self.exec("i")
            if "Current SPSR" in ret:
                self.lhbdi.read_until_prompt(self.prompt)
                return ret
            elif "Current CCSRBAR" in ret:
                self.lhbdi.read_until_prompt(self.prompt)
                return ret
            elif "running" in ret:
                if check_run == True:
                    self.bdi_reset_board()
                else:
                    self.lhbdi.read_until_prompt(self.prompt)
                    return ret
            elif "CONFIG: cannot open" in ret:
                tbot.log.message(f"BDI has wrong config file, try to set {self.bdicfgfile}")
                self.exec("config", self.bdicfgfile)
                # bdi reboots now
                self.lhbdi.close()
                self.lhbdi = self.lh.new_channel("telnet", self.bdiname)
                self.lhbdi.read_until_prompt(self.prompt)
                self.check_ready()
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
        self.lh = lh
        self.lhbdi = lh.new_channel("telnet", self.bdiname)
        self.lhbdi.read_until_prompt(self.prompt)
        self.check_ready()
        ret = self.exec("config")
        if self.bdicfgfile not in ret:
            raise RuntimeError("BDI has wrong config file")

    @tbot.testcase
    def bdi_reset_board(
        self,
    ) -> None:
        ret = self.exec("res", "halt")
        self.check_ready()

    @tbot.testcase
    def bdi_reset_board_run(
        self,
    ) -> None:
        ret = self.exec("res", "run")
        self.check_ready(check_run=False)

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
