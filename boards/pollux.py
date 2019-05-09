import abc
import contextlib
import typing
import tbot
import time
from tbot.machine import board, channel, linux, connector
from tbot.tc import uboot, git, kconfig
from tbot.tc import uboot, git, kconfig
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir + '/tc/commonhelper')
import generic as ge

class Board(connector.ConsoleConnector, board.PowerControl, board.Board):
    connect_wait = 0.0

    def _get_boardname(self):
        if self.name == "wandboard":
            return "wandboard_dl"
        elif self.name == "taurus":
            return "at91_taurus"
        elif self.name == "socrates":
            return "socrates-abb"
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

    @contextlib.contextmanager
    def kermit_connect(self, mach: linux.LinuxShell) -> channel.Channel:
        KERMIT_PROMPT = b"C-Kermit>"
        n = self._get_boardname()
        cfg_file = f"/home/{self.host.username}/kermrc_{n}"
        ch = mach.open_channel("kermit", cfg_file)
        try:
            yield ch
        finally:
            ch.sendcontrol("\\")
            ch.send("C")
            ch.read_until_prompt(KERMIT_PROMPT)
            ch.sendline("exit")
            ch.sendline("OK")

    @contextlib.contextmanager
    def telnet_connect(self, mach: linux.LinuxShell) -> channel.Channel:
        n = self._get_boardname()
        TELNET_PROMPT = "> "
        ch = mach.open_channel("connect", n)
        try:
            yield ch
        finally:
            ch.send('\x1d')
            ch.read_until_prompt(TELNET_PROMPT)
            ch.sendline("quit")


    def ssh_connect(self) -> channel.Channel:
        return mach.open_channel("ssh", "hs@" + self.host.boardip[self.name])

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        if self.name == 'piinstall':
            return self.ssh_connect(mach)
        elif self.name == 'aristainetos':
            return self.telnet_connect(mach)
        else:
            return self.kermit_connect(mach)

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
            #lh.name == self.lab_name
            lh.name == "pollux"
        ), f"{lh!r} is the wrong lab for this board! (Expected 'pollux')"
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
