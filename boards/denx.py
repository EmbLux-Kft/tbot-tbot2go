import tbot
from tbot.machine import channel
from tbot.machine import board
from tbot.tc import uboot

class DenxBoard(board.Board):
    connect_wait = 0.0

    def _get_boardname(self):
        if self.name == "wandboard":
            n = "wandboard_dl"
        elif self.name == "taurus":
            n = "at91_taurus"
        else:
            n = self.name
        return n

    def poweron(self) -> None:
        n = self._get_boardname()
        self.lh.exec0("remote_power", n, "on")

    def poweroff(self) -> None:
        n = self._get_boardname()
        self.lh.exec0("remote_power", n, "off")

    def connect(self) -> channel.Channel:
        n = self._get_boardname()
        return self.lh.new_channel("connect", n)

    def console_check(self) -> None:
        n = self._get_boardname()
        ret = self.lh.exec0("remote_power", n, "-l")
        if "off" in ret or "OFF" in ret:
            pass
        else:
            raise RuntimeError("Board is already on, someone might be using it!")
