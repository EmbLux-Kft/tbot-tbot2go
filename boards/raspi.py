from tbot.machine import channel
from tbot.machine import board
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

    def poweron(self) -> None:
        if self.name == 'XXX':
            self.lh.exec0("power.py", "-p", "XXX", "-s", "on")
        else:
            raise RuntimeError("Board ", self.name, " not configured")

    def poweroff(self) -> None:
        if self.name == 'XXX':
            self.lh.exec0("power.py", "-p", "XXX", "-s", "off")
        else:
            raise RuntimeError("Board ", self.name, " not configured")

    def connect(self) -> channel.Channel:
        KERMIT_PROMPT = b"C-Kermit>"
        if self.name == 'XXX':
            cfg_file = "/home/pi/kermrc_XXX"
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
