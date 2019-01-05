import functools
import getpass
import pathlib
import typing
import tbot
from tbot.machine import connector, linux, board
import builders

class SmalllaptopLab(connector.ParamikoConnector, linux.Bash, linux.Lab, linux.Builder):
    name = "small-lab"
    hostname = "192.168.1.105"
    #hostname = "192.168.3.10"
    username = "hs"

    serverip = "192.168.3.10"
    netmask = "255.255.255.0"
    ethaddr = {}
    ethaddr["wandboard"] = "00:1f:7b:b2:00:0f"
    boardip = {}
    boardip = {
        "wandboard": "192.168.3.20",
    }
    tftproot = "/var/lib/tftpboot"
    ub_load_board_env_subdir = "tbot"

    @property
    def get_boardname(self) -> str:
        if tbot.selectable.Board.name == "taurus":
            return "at91_taurus"
        elif tbot.selectable.Board.name == "wandboard":
            return "wandboard"

        return tbot.selectable.Board.name

    @property
    def nfs_root(self) -> "linux.Path[SmalllaptopLab]":
        return linux.Path(self, f"/work/tbot2go/nfs")

    @property
    def tftp_root_path(self) -> "linux.Path[SmalllaptopLab]":
        """
        returns root tftp path
        """
        return linux.Path(self, self.tftproot)

    @property
    def tftp_dir_board(self) -> "linux.Path[SmalllaptopLab]":
        """
        returns tftp path for u-boot tftp command
        """
        return linux.Path(self, f"{self.get_boardname}/tbot")

    @property
    def yocto_result_dir(self) -> "linux.Path[SmalllaptopLab]":
        return linux.Path(self, f"{self.tftproot}/" + tbot.selectable.Board.name + "/tbot/yocto_results")

    @property
    def workdir(self) -> "linux.Path[SmalllaptopLab]":
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

    def build(self) -> linux.Builder:
        if "pollux-build" in tbot.flags:
            return builders.PolluxSSH(self)
        elif "xpert-build" in tbot.flags:
            return builders.XpertSSH(self)
        elif "hercules-build" in tbot.flags:
            return builders.HerculesSSH(self)
        elif "hercules-1604-build" in tbot.flags:
            return builders.Hercules1604SSH(self)
        elif "smalllaptop-build" in tbot.flags:
            return self
        elif "threadripper-build" in tbot.flags:
            return builders.ThreadripperSSH(self)
        elif "threadripper-1604-build" in tbot.flags:
            return builders.Threadripper1604SSH(self)
        elif "threadripper-1604-kas-build" in tbot.flags:
            return builders.Threadripper1604kasSSH(self)
        elif "xmg-build" in tbot.flags:
            return builders.xmgSSH(self)
        raise RuntimeError ("build Machine not specified")

LAB = SmalllaptopLab
