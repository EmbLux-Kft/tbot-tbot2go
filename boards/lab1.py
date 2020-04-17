import abc
import contextlib
import typing
import tbot
import time
from tbot.machine import board, channel, linux, connector
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
            n = "wandboard"
            self.pin = "3"
        elif self.name == "k30rf":
            if "v4" in tbot.flags:
                n = "k30rf-v4"
                self.pin = "4"
            else:
                raise RuntimeError("Board ", self.name, " not configured")

        else:
            raise RuntimeError("Board ", self.name, " not configured")

        return n

    def poweron(self) -> None:
        n = self._get_boardname()
        # eventuell /home/tbot/sources/remote_power
        self.host.exec0("sudo", "sispmctl", "-D", "01:01:56:a2:f1", "-o", self.pin)

        td = ge.get_path(self.host.toolsdir)
        yrd = ge.get_path(self.host.yocto_result_dir)
        if "splusbloader" in tbot.flags:
            loop = True
            while loop:
                try:
                    self.host.exec0("sudo", f"{td}/imx_usb_loader/imx_usb", f"{yrd}/SPL-spi.signed")
                    loop = False
                except:
                    time.sleep(2)
                    pass
        if "usbloader" in tbot.flags:
            loop = True
            while loop:
                try:
                    self.host.exec0("sudo", f"{td}/imx_usb_loader/imx_usb", f"{yr}/SPL-spi.signed")
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



        return

    def poweroff(self) -> None:
        self.host.exec0("sudo", "sispmctl", "-D", "01:01:56:a2:f1", "-f", self.pin)
        return

    @contextlib.contextmanager
    def kermit_connect(self, mach: linux.LinuxShell) -> channel.Channel:
        KERMIT_PROMPT = b"C-Kermit>"
        n = self._get_boardname()
        if self.name == 'k30rf':
            cfg_file = f"/home/{self.host.username}/kermrc_{n}"
        elif self.name == 'wandboard':
            cfg_file = f"/home/{self.host.username}/kermrc_{n}"
        else:
            raise RuntimeError("Board ", self.name, " console not configured")
        ch = mach.open_channel("kermit", cfg_file)
        try:
            yield ch
        finally:
            ch.sendcontrol("\\")
            ch.send("C")
            ch.read_until_prompt(KERMIT_PROMPT)
            ch.sendline("exit")
            # give usb2serial adapter some time
            time.sleep(5)

    def ssh_connect(self) -> channel.Channel:
        return mach.open_channel("ssh", "hs@" + self.host.boardip[self.name])

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        if self.name == 'piinstall':
            return self.ssh_connect(mach)
        else:
            return self.kermit_connect(mach)

    def console_check(self) -> None:
        n = self._get_boardname()
        ret = self.host.exec0("sudo", "sispmctl", "-D", "01:01:56:a2:f1", "-g", self.pin)
        if "off" not in ret:
            if self.name == 'wandboard':
                ret = self.host.exec0("sispmctl", "-D", "01:01:56:a2:f1", "-f", self.pin)
                time.sleep(2)
                ret = self.host.exec0("sispmctl", "-D", "01:01:56:a2:f1", "-o", self.pin)
            else:
                raise RuntimeError("Board is already on, someone might be using it!")

    def __init__(self, lh: linux.LinuxShell) -> None:
        # Check lab
        assert (
            # lh.name == self.lab_name()
            lh.name == "lab1"
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
    if tbot.selectable.LabHost.name in ["small-lab", "lab1"]:
        remote = "/home/hs/data/Entwicklung/sources/u-boot"
        ub_patches_path = None

    if tbot.selectable.LabHost.name in ["pollux", "hercules"]:
        remote = "/home/git/u-boot.git"

    def do_configure(self, bh: BH, repo: git.GitRepository[BH]) -> None:
        super().do_configure(bh, repo)

        tbot.log.message("Patching U-Boot config ...")

        # Add local-version tbot
        kconfig.set_string_value(repo / ".config", "CONFIG_LOCALVERSION", "-tbot")

FLAGS = {
        "usbloader" : "load SPL / U-Boot with imx_usb_loader",
        "splusbloader" : "load SPL with imx_usb_loader"
}
