import tbot
from tbot.machine import channel
from tbot.machine import board
from tbot.tc import uboot
from tbot.machine.board import special
from tbot.machine import linux

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir + '/tc/commonhelper')
import generic as ge

class Tbot2go2Board(board.Board):
    connect_wait = 1.0
    pin = "4"
    boardlabname = "imx8qxpmek"

    def _get_boardname(self):
        return self.name

    def poweron(self) -> None:
        if "nopoweroff" in tbot.flags:
            return

        if self.name == "bbb":
            if "bootmodesd" in tbot.flags:
                self.lh.set_bootmode("sd")
            if "bootmodeemmc" in tbot.flags:
                self.lh.set_bootmode("emmc")

        if self.name == 'imx8qxpmek':
            self.lh.exec0("sudo", "/home/hs/pyrelayctl/examples/relctl.py","-D", "A907PJK8", "-o", self.pin)
        else:
            raise RuntimeError("Board ", self.name, " not configured")

    def poweroff(self) -> None:
        if "nopoweroff" in tbot.flags:
            return
        if self.name == 'imx8qxpmek':
            self.lh.exec0("sudo", "/home/hs/pyrelayctl/examples/relctl.py","-D", "A907PJK8", "-f", self.pin)
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
        if self.name == 'imx8qxpmek':
            cfg_file = f"/home/{self.lh.username}/kermrc_imx8qxpmek"
        else:
            raise RuntimeError("Board ", self.name, " console not configured")
        ch = self.lh.new_channel("kermit", cfg_file)

        # Receive at max the prompt or timeout after 5 seconds
        raw = b""
        try:
            loop = True
            while loop:
                raw += ch.recv_n(1, timeout=2.0)
                # bbb send 0x00 endless if of ...
                if b"0" in raw:
                    return ch
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

FLAGS = {
        "bootmodesd" : "Boot with bootmode sd",
        "bootmodeemmc" : "Boot with bootmode emmc",
}
