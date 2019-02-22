import tbot
from tbot.machine import channel
from tbot.machine import board
from tbot.tc import uboot

class DenxBoard(board.Board):
    connect_wait = 0.0

    def _get_boardname(self):
        if self.name == "wandboard":
            return "wandboard_dl"
        elif self.name == "taurus":
            return "at91_taurus"
        return self.name

    def poweron(self) -> None:
        self.lh.exec0("remote_power", self._get_boardname(), "on")

    def poweroff(self) -> None:
        if "nopoweroff" in tbot.flags:
            return
        n = self._get_boardname()
        self.lh.exec0("remote_power", self._get_boardname(), "off")

    def connect(self) -> channel.Channel:
        return self.lh.new_channel("connect", self._get_boardname())

    def console_check(self) -> None:
        if "nopoweroff" in tbot.flags:
            return
        n = self._get_boardname()
        if "off" not in self.lh.exec0("remote_power", self._get_boardname(), "-l"):
            raise RuntimeError("Board is already on, someone might be using it!")

