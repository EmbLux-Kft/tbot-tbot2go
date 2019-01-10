import tbot
from tbot.machine import channel
from tbot.machine import board
from tbot.tc import uboot

class StefanoBoard(board.Board):
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
        self.lh.exec0("remote_power", n, "on")

    def poweroff(self) -> None:
        n = self._get_boardname()
        self.lh.exec0("remote_power", n, "off")

    def connect(self) -> channel.Channel:
        #n = self._get_boardname()
        # kermit ?
        #return self.lh.new_channel("connect", n)
        KERMIT_PROMPT = b"C-Kermit>"
            if self.name == 'wandboard':
                n = _get_boardname()
                cfg_file = f"/home/{tbot.selectable.LabHost.username}/kermrc_{n}"
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
        if "off" not in self.lh.exec0("remote_power", n, "-l"):
            raise RuntimeError("Board is already on, someone might be using it!")


class StefanoUBootBuildInfo(uboot.BuildInfo):
    if tbot.selectable.LabHost.name == "embedded-lab":
        uboot_remote = "/home/tbot/sources/u-boot"
