import typing
import tbot
from tbot.machine import board, channel, linux, connector
from tbot.tc import uboot, git, kconfig
import time

class Board(connector.ConsoleConnector, board.PowerControl, board.Board):
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
                self.host.set_bootmode("sd")
            if "bootmodespi" in tbot.flags:
                self.host.set_bootmode("spi")
        self.host.exec0("remote_power", self._get_boardname(), "on")

    def poweroff(self) -> None:
        if "nopoweroff" in tbot.flags:
            return
        n = self._get_boardname()
        self.host.exec0("remote_power", self._get_boardname(), "off")
        if self.name == "aristainetos":
            time.sleep(2)

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        if "no_console_check" in tbot.flags:
            return

        return mach.open_channel("connect", self._get_boardname())

    def power_check(self) -> bool:
        if "no_console_check" in tbot.flags:
            return True

        if "nopoweroff" in tbot.flags:
            return True

        n = self._get_boardname()
        ret = self.host.exec0("remote_power", n, "-l")
        if "off" in ret or "OFF" in ret:
            pass
        else:
           raise RuntimeError("Board is already on, someone might be using it!")

        return True

    def __init__(self, lh: linux.LinuxShell) -> None:
        # Check lab
        assert (
            lh.name == "pollux"
        ), f"{lh!r} is the wrong lab for this board! (Expected '{self.lab_name}')"
        super().__init__(lh)

B = typing.TypeVar("B", bound=Board)
BH = typing.TypeVar("BH", bound=linux.Builder)

class UBootMachine(board.Connector, board.UBootAutobootIntercept, board.UBootShell):
    def flash(self, repo: git.GitRepository) -> None:
        """Flash a new U-Boot version that was built in the given repo."""
        raise NotImplementedError("U-Boot flashing was not implemented for this board!")

    def lab_network(self) -> None:
        """Setup the network connection in the selected lab."""
        self.host = getattr(self, "host")
        try:
            getattr(self.host, "uboot_network_setup")(self)
        except AttributeError:
            raise Exception(
                f"The lab-host {self.host!r} does not seem to support uboot network setup!"
            )

class UBootBuilder(uboot.UBootBuilder):
    if tbot.selectable.LabHost.name in ["pollux", "hercules"]:
        remote = "/home/git/u-boot.git"

    def do_configure(self, bh: BH, repo: git.GitRepository[BH]) -> None:
        super().do_configure(bh, repo)

        tbot.log.message("Patching U-Boot config ...")

        # Add local-version tbot
        kconfig.set_string_value(repo / ".config", "CONFIG_LOCALVERSION", "-tbot")

        # Tab completion
        kconfig.enable(repo / ".config", "CONFIG_AUTO_COMPLETE")

        # Enable configs for network setup
        kconfig.enable(repo / ".config", "CONFIG_CMD_NET")
        kconfig.enable(repo / ".config", "CONFIG_CMD_DHCP")
        kconfig.enable(repo / ".config", "CONFIG_CMD_MII")
        kconfig.enable(repo / ".config", "CONFIG_BOOTP_PREFER_SERVERIP")
        kconfig.disable(repo / ".config", "CONFIG_BOOTP_BOOTPATH")

FLAGS = {
        "bootmodesd" : "Boot with bootmode sd",
        "bootmodespi" : "Boot with bootmode spi",
        "no_console_check" : "do not check if console is used",
}
