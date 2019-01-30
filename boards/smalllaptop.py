import tbot
import time
from tbot.machine import channel
from tbot.machine import board
from tbot.tc import uboot

class SmalllaptopBoard(board.Board):
    connect_wait = 0.0

    def _get_boardname(self):
        if self.name == "wandboard":
            n = "wandboard"
        else:
            n = self.name
        return n

    def poweron(self) -> None:
        n = self._get_boardname()
        # eventuell /home/tbot/sources/remote_power
        self.lh.exec0("sispmctl", "-D", "01:01:56:a2:f1", "-o", "3")

    def poweroff(self) -> None:
        n = self._get_boardname()
        self.lh.exec0("sispmctl", "-D", "01:01:56:a2:f1", "-f", "3")

    def connect(self) -> channel.Channel:
        # need here a small sleep, to calm down serial driver
        time.sleep(2)
        KERMIT_PROMPT = b"C-Kermit>"
        if self.name == 'wandboard':
            n = self._get_boardname()
            cfg_file = f"/home/{tbot.selectable.LabHost.username}/data/Entwicklung/messe/2019/kermrc_{n}"
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

    def console_check(self) -> None:
        n = self._get_boardname()
        ret = self.lh.exec0("sispmctl", "-D", "01:01:56:a2:f1", "-g", "3")
        if "off" not in ret:
            raise RuntimeError("Board is already on, someone might be using it!")


class SmalllaptopUBootBuildInfo(uboot.BuildInfo):
    if tbot.selectable.LabHost.name == "small-lab":
        uboot_remote = "/home/hs/data/Entwicklung/sources/u-boot"
        ub_patches_path = None
