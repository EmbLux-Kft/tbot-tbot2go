import typing
import tbot
from tbot.machine import board, channel, linux
from tbot.tc import uboot, git, kconfig
import time

class DenxBoard(board.Board):
    connect_wait = 0.0

    def _get_boardname(self):
        if self.name == "wandboard":
            return "wandboard_dl"
        elif self.name == "taurus":
            return "at91_taurus"
        return self.name

    def poweron(self) -> None:
        if "nopoweroff" in tbot.flags:
            return

        if self.name == "aristainetos":
            if "bootmodesd" in tbot.flags:
                self.lh.set_bootmode("sd")
            if "bootmodespi" in tbot.flags:
                self.lh.set_bootmode("spi")
        self.lh.exec0("remote_power", self._get_boardname(), "on")

    def poweroff(self) -> None:
        if "nopoweroff" in tbot.flags:
            return
        n = self._get_boardname()
        self.lh.exec0("remote_power", self._get_boardname(), "off")
        if self.name == "aristainetos":
            time.sleep(2)

    def connect(self) -> channel.Channel:
        if "no_console_check" in tbot.flags:
            return

        return self.lh.new_channel("connect", self._get_boardname())

    def console_check(self) -> None:
        if "no_console_check" in tbot.flags:
            return

        if "nopoweroff" in tbot.flags:
            return
        n = self._get_boardname()
        ret = self.lh.exec0("remote_power", n, "-l")
        if "off" in ret or "OFF" in ret:
            pass
        else:
           raise RuntimeError("Board is already on, someone might be using it!")

BH = typing.TypeVar("BH", bound=linux.BuildMachine)

class UBootBuilder(uboot.UBootBuilder):
    if tbot.selectable.LabHost.name in ["pollux", "hercules"]:
        remote = "git@gitlab.denx.de:abb/aristainetos-uboot.git"

    def do_configure(self, bh: BH, repo: git.GitRepository[BH]) -> None:
        super().do_configure(bh, repo)

        tbot.log.message("Patching U-Boot config ...")

        # Add local-version tbot
        kconfig.set_string_value(repo / ".config", "CONFIG_LOCALVERSION", "-tbot")

        # Tab completion
        kconfig.enable(repo / ".config", "CONFIG_AUTO_COMPLETE")

        # Enable configs for network setup
        kconfig.enable(repo / ".config", "CONFIG_CMD_DHCP")

FLAGS = {
        "bootmodesd" : "Boot with bootmode sd",
        "bootmodespi" : "Boot with bootmode spi",
        "no_console_check" : "do not check if console is used",
}
