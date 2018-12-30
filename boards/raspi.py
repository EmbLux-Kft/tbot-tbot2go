import tbot
from tbot.machine import channel
from tbot.machine import board
from tbot.tc import uboot

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir + '/tc/commonhelper')
import generic as ge

class Tbot2goUBootBuildInfo(uboot.BuildInfo):
    print(" ===== tbot.selectable.LabHost.name ", tbot.selectable.LabHost.name)
    if tbot.selectable.LabHost.name == "pollux":
        uboot_remote = "/home/git/u-boot.git"
    elif tbot.selectable.LabHost.name == "tbot2go":
        uboot_remote = "/home/hs/data/Entwicklung/work/hs/tbot2go/sources/u-boot"

class Tbot2goBoard(board.Board):
    connect_wait = 1.0
    pin = "3"
    boardlabname = "k30rf"
    if "16mb" in tbot.flags:
        pin = "4"
        boardlabname = "k30rf-16mb"

    def poweron(self) -> None:
        if "nopoweroff" in tbot.flags:
            return
        if self.name == 'k30rf':
            #self.lh.exec0("power.py", "-p", "19", "-s", "on")
            self.lh.exec0("sudo", "/work/tbot2go/tbot/src/pyrelayctl/examples/relctl.py","-D", "A907QJT3", "-o", self.pin)
        elif self.name == 'h03pl086':
            self.lh.exec0("power.py", "-p", "14", "-s", "on")
        elif self.name == 'piinstall':
            pass
        else:
            raise RuntimeError("Board ", self.name, " not configured")

    def poweroff(self) -> None:
        if "nopoweroff" in tbot.flags:
            return
        if self.name == 'k30rf':
            #self.lh.exec0("power.py", "-p", "19", "-s", "off")
            self.lh.exec0("sudo", "/work/tbot2go/tbot/src/pyrelayctl/examples/relctl.py","-D", "A907QJT3", "-f", self.pin)
        elif self.name == 'h03pl086':
            self.lh.exec0("power.py", "-p", "14", "-s", "off")
        elif self.name == 'piinstall':
            pass
        else:
            raise RuntimeError("Board ", self.name, " not configured")

    def console_check(self) -> None:
        if "nopoweroff" in tbot.flags:
            return

    def ssh_connect(self) -> channel.Channel:
        ch = self.lh.new_channel("ssh", "hs@" + tbot.selectable.LabHost.boardip[self.name])
        return ch

    def kermit_connect(self) -> channel.Channel:
        KERMIT_PROMPT = b"C-Kermit>"
        if self.name == 'k30rf':
            cfg_file = "/home/pi/kermrc_" + self.boardlabname
        elif self.name == 'h03pl086':
            cfg_file = "/home/pi/kermrc_h03pl086"
        else:
            raise RuntimeError("Board ", self.name, " console not configured")
        ch = self.lh.new_channel("kermit", cfg_file)

        # Receive at max the prompt or timeout after 5 seconds
        raw = b""
        try:
            loop = True
            while loop:
                raw += ch.recv_n(1, timeout=2.0)
        except TimeoutError:
            pass
        except TimeoutException:
            pass

        if KERMIT_PROMPT in raw:
            raise RuntimeError("Could not get console for ", self.name)

        return ch

    def connect(self) -> channel.Channel:
        if self.name == 'piinstall':
            return self.ssh_connect()
        else:
            return self.kermit_connect()
