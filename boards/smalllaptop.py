import abc
import contextlib
import typing
import tbot
import time
from tbot.machine import board, channel, linux, connector
from tbot.tc import uboot, git, kconfig
import time

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir + '/tc/commonhelper')
import generic as ge

class Board(connector.ConsoleConnector, board.PowerControl, board.Board):
    connect_wait = 0.0
    KERMIT_PROMPT = b"C-Kermit>"

    def _get_boardname(self):
        return self.name

    def poweron(self) -> None:
        # eventuell /home/tbot/sources/remote_power
        self.host.exec0("sispmctl", "-D", "01:01:56:a2:f1", "-o", "3")
        return

    def poweroff(self) -> None:
        self.host.exec0("sispmctl", "-D", "01:01:56:a2:f1", "-f", "3")
        return

    def ssh_connect(self, mach: linux.LinuxShell) -> channel.Channel:
        return mach.open_channel("ssh", "hs@" + self.host.boardip[self.name])

    @contextlib.contextmanager
    def kermit_connect(self, mach: linux.LinuxShell) -> channel.Channel:
        KERMIT_PROMPT = b"C-Kermit>"
        if self.name == 'imx8qxpmek':
            cfg_file = f"/home/{self.host.username}/kermrc_imx8qxpmek"
        elif self.name == 'wandboard':
            cfg_file = f"/home/{tbot.selectable.LabHost.username}/data/Entwicklung/messe/2019/kermrc_wandboard"
        else:
            raise RuntimeError("Board ", self.name, " console not configured")
        ch = mach.open_channel("kermit", cfg_file)
        try:
            try:
                ret = ch.read(150, timeout=2)
                buf = ret.decode(errors="replace")
                if "Locked" in buf:
                    raise RuntimeError(f"serial line is locked {buf}")
                if "C-Kermit" in buf:
                    raise RuntimeError(f"serial line is locked {buf}")
            except TimeoutError:
                pass

            yield ch
        finally:
            ch.send(chr(28) + "C")
            ch.sendline("exit")
            # give usb2serial adapter some time
            time.sleep(2)

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        if self.name == 'piinstall':
            return self.ssh_connect(mach)
        else:
            return self.kermit_connect(mach)

    def __init__(self, lh: linux.LinuxShell) -> None:
        # Check lab
        assert (
            # lh.name == self.lab_name()
            lh.name == "small-lab"
        ), f"{lh!r} is the wrong lab for this board! (Expected '{self.lab_name}')"
        super().__init__(lh)

    def power_check(self) -> bool:
        ret = self.host.exec0("sispmctl", "-D", "01:01:56:a2:f1", "-g", "3")
        if "off" not in ret:
            ret = self.host.exec0("sispmctl", "-D", "01:01:56:a2:f1", "-f", "3")
            time.sleep(2)
            ret = self.host.exec0("sispmctl", "-D", "01:01:56:a2:f1", "-o", "3")
            raise RuntimeError("Board is already on, someone might be using it!")
        return True

B = typing.TypeVar("B", bound=Board)
BH = typing.TypeVar("BH", bound=linux.Builder)

class UBootMachine(board.Connector, board.UBootAutobootIntercept, board.UBootShell):
    def flash(self, repo: git.GitRepository) -> None:
        """Flash a new U-Boot version that was built in the given repo."""
        raise NotImplementedError("U-Boot flashing was not implemented for this board!")

    def lab_network(self) -> None:
        """Setup the network connection in the selected lab."""
        self.host = getattr(self, "host")
        print("----------- NETWORK SETUP -------------")
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


