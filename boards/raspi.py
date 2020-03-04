import abc
import contextlib
import typing
import tbot
from tbot.machine import board, channel, linux, connector
from tbot.tc import uboot, git
import time

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir + '/tc/commonhelper')
import generic as ge

class Board(connector.ConsoleConnector, board.PowerControl, board.Board):
    connect_wait = 1.0
    pin = "3"
    boardlabname = "k30rf"
    if "16mb" in tbot.flags:
        pin = "4"
        boardlabname = "k30rf-16mb"
    if "sd" in tbot.flags:
        pin = "3"
        boardlabname = "k30rf-16mb-sd"

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

        if self.name == 'k30rf':
            #self.lh.exec0("power.py", "-p", "19", "-s", "on")
            self.host.exec0("sudo", "/work/tbot2go/tbot/src/pyrelayctl/examples/relctl.py","-D", "A907QJT3", "-o", self.pin)
        elif self.name == 'bbb':
            ge.lx_gpio(self.host, "4", "on")
        elif self.name == 'h03pl086':
            self.host.exec0("power.py", "-p", "14", "-s", "on")
        elif self.name == 'piinstall':
            pass
        else:
            raise RuntimeError("Board ", self.name, " not configured")
        if "splusbloader" in tbot.flags:
            loop = True
            while loop:
                try:
                    self.host.exec0("sudo", "/home/pi/tbot2go/src/imx_usb_loader/imx_usb", "/srv/tftpboot/k30rf/tbot/yocto_results/SPL-spi.signed")
                    loop = False
                except:
                    time.sleep(2)
                    pass
        if "usbloader" in tbot.flags:
            loop = True
            while loop:
                try:
                    self.host.exec0("sudo", "/home/pi/tbot2go/src/imx_usb_loader/imx_usb", "/srv/tftpboot/k30rf/tbot/yocto_results/SPL-spi.signed")
                    loop = False
                except:
                    time.sleep(2)
                    pass

            loop = True
            while loop:
                try:
                    self.host.exec0("sudo", "/home/pi/tbot2go/src/imx_usb_loader/imx_usb", "/srv/tftpboot/k30rf/tbot/yocto_results/u-boot-ivt.img-spi.signed")
                    loop = False
                except:
                    time.sleep(2)
                    pass

    def poweroff(self) -> None:
        if "nopoweroff" in tbot.flags:
            return
        if self.name == 'k30rf':
            self.host.exec0("sudo", "/work/tbot2go/tbot/src/pyrelayctl/examples/relctl.py","-D", "A907QJT3", "-f", self.pin)
        elif self.name == 'bbb':
            ge.lx_gpio(self.host, "4", "off")
        elif self.name == 'h03pl086':
            self.host.exec0("power.py", "-p", "14", "-s", "off")
        elif self.name == 'piinstall':
            pass
        else:
            raise RuntimeError("Board ", self.name, " not configured")

    def power_check(self) -> bool:
        if "nopoweroff" in tbot.flags:
            return True
        # check if power is on -> board is in use
        # ToDo
        return True

    def ssh_connect(self) -> channel.Channel:
        return mach.open_channel("ssh", "hs@" + self.host.boardip[self.name])

    @contextlib.contextmanager
    def kermit_connect(self, mach: linux.LinuxShell) -> channel.Channel:
        KERMIT_PROMPT = b"C-Kermit>"
        if self.name == 'k30rf':
            cfg_file = f"/home/{self.host.username}/kermrc_{self.boardlabname}"
        elif self.name == 'bbb':
            cfg_file = f"/home/{self.host.username}/kermrc_bbb"
        elif self.name == 'h03pl086':
            cfg_file = f"/home/{self.host.username}/kermrc_h03pl086"
        else:
            raise RuntimeError("Board ", self.name, " console not configured")
        ch = mach.open_channel("kermit", cfg_file)
        try:
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
            lh.name == "tbot2go"
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
        "usbloader" : "load SPL / U-Boot with imx_usb_loader",
        "splusbloader" : "load SPL with imx_usb_loader"
}
