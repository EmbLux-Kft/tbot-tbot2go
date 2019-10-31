import abc
import typing
import tbot
from tbot.machine import board, channel, linux, connector
from tbot.tc import uboot, git, kconfig

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir + '/tc/commonhelper')
import generic as ge

class Board(connector.ConsoleConnector, board.PowerControl, board.Board):
    connect_wait = 1.0

#    @property
#    @abc.abstractmethod
#    def lab_name(self) -> str:
#        return "tbot2go2"

    def _get_boardname(self):
        return self.name

    def poweron(self) -> None:
        if "nopoweroff" in tbot.flags:
            return

        if self.name == "bbb":
            if "bootmodesd" in tbot.flags:
                self.host.set_bootmode("sd")
            if "bootmodeemmc" in tbot.flags:
                self.host.set_bootmode("emmc")

        if self.name == 'imx8qxpmek':
            self.host.exec0("sudo", "/home/hs/pyrelayctl/examples/relctl.py","-D", "A907PJK8", "-o", "4")
        else:
            raise RuntimeError("Board ", self.name, " not configured")

    def poweroff(self) -> None:
        if "nopoweroff" in tbot.flags:
            return
        if self.name == 'imx8qxpmek':
            self.host.exec0("sudo", "/home/hs/pyrelayctl/examples/relctl.py","-D", "A907PJK8", "-f", "4")
        else:
            raise RuntimeError("Board ", self.name, " not configured")

    def power_check(self) -> bool:
        if "nopoweroff" in tbot.flags:
            return True
        # check if power is on -> board is in use
        # ToDo
        return True

    def ssh_connect(self, mach: linux.LinuxShell) -> channel.Channel:
        return mach.open_channel("ssh", "hs@" + self.host.boardip[self.name])

    def kermit_connect(self, mach: linux.LinuxShell) -> channel.Channel:
        KERMIT_PROMPT = b"C-Kermit>"
        if self.name == 'imx8qxpmek':
            cfg_file = f"/home/{self.host.username}/kermrc_imx8qxpmek"
        else:
            raise RuntimeError("Board ", self.name, " console not configured")
        ch = mach.open_channel("kermit", cfg_file)

        # Receive at max the prompt or timeout after 5 seconds
        #raw = b""
        #try:
        #    loop = True
        #    while loop:
        #        raw += ch.recv_n(1, timeout=2.0)
        #        # bbb send 0x00 endless if of ...
        #        if b"0" in raw:
        #            return ch
        #except TimeoutError:
        #    pass
        # wo ist das nun ?
        #except TimeoutException:
        #    pass

        #if KERMIT_PROMPT in raw:
        #    raise RuntimeError("Could not get console for ", self.name)

        return ch

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        if self.name == 'piinstall':
            return self.ssh_connect(mach)
        else:
            return self.kermit_connect(mach)

    def __init__(self, lh: linux.LinuxShell) -> None:
        # Check lab
        assert (
            # lh.name == self.lab_name()
            lh.name == "tbot2go2"
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


FLAGS = {
        "bootmodesd" : "Boot with bootmode sd",
        "bootmodeemmc" : "Boot with bootmode emmc",
}