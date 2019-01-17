import typing
import tbot
from tbot.machine.linux import lab
from tbot.machine import linux

class SmalllaptopLab(lab.SSHLabHost, linux.BuildMachine):
    name = "small-lab"
    # oder 192.168.2.177 ?
    hostname = "192.168.1.106"
    username = "hs"

    serverip = "192.168.2.177"
    netmask = "255.255.255.0"
    boardip = {}
    boardip["wandboard"] = "192.168.2.238"
    ethaddr = {}
    ethaddr["wandboard"] = "00:1f:7b:b2:00:0f"

    @property
    def get_boardname(self) -> str:
        if tbot.selectable.Board.name == "taurus":
            return "at91_taurus"
        elif tbot.selectable.Board.name == "wandboard":
            return "wandboard"

        return tbot.selectable.Board.name

    @property
    def tftp_dir(self) -> "linux.path.Path[SmallLab]":
        return linux.Path(self, f"/srv/tftpboot/" + self.get_boardname + "/tbot")

    @property
    def workdir(self) -> "linux.path.Path[SmallLab]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot-workdir")

    @property
    def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
        return {
            "bootlin-armv5-eabi": linux.build.EnvSetBootlinToolchain(
                arch = "armv5-eabi",
                libc = "glibc",
                typ = "stable",
                date = "2018.11-1",
                ),
            "linaro-gnueabi": linux.build.EnvSetLinaroToolchain(
                host_arch = "i686",
                arch = "arm-linux-gnueabi",
                date = "2018.05",
                gcc_vers = "7.3",
                gcc_subvers = "1",
                ),
        }

    def build(self) -> linux.BuildMachine:
        return self

LAB = SmalllaptopLab
