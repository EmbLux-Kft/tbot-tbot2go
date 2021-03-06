import functools
import getpass
import pathlib
import typing
import tbot
import builders
from tbot.machine import channel
from tbot.machine.linux import lab
from tbot.machine import linux
import builders

class XpertLab(lab.SSHLabHost, linux.BuildMachine):
    name = "xpert"
    hostname = "xpert.denx.de"

    serverip = "192.168.0.4"
    netmask = "255.255.128.0"
    boardip = {
        "sanvito": "192.168.1.11",
        "sanvito-b": "192.168.1.12",
        "dbbasic": "192.168.0.2",
    }
    ethaddr = {
        "sanvito": "1e:a7:65:aa:71:59",
    }

    @property
    def get_boardname(self) -> str:
        if tbot.selectable.Board.name == "taurus":
            return "at91_taurus"
        elif tbot.selectable.Board.name == "wandboard":
            return "wandboard_dl"

        return tbot.selectable.Board.name

    @property
    def yocto_result_dir(self) -> "linux.path.Path[XpertLab]":
        return linux.Path(self, f"/tftpboot/{tbot.selectable.Board.name}/yocto_results")

    @property
    def workdir(self) -> "linux.path.Path[XpertLab]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot-workdir")

    @property
    def tftp_dir(self) -> "linux.path.Path[XpertLab]":
        return linux.Path(self, f"/tftpboot/{self.get_boardname}/{self.username}/tbot")

    @property
    def tftp_dir_board(self) -> "linux.path.Path[XpertLab]":
        return linux.Path(self, f"{self.get_boardname}/{self.username}/tbot")

    @property
    def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
        return {
            "generic-armv7a": linux.build.EnvScriptToolchain(
                linux.Path(
                    self,
                    "/opt/eldk/build/work/hws/lweimx6/sdk/environment-setup-armv7a-neon-poky-linux-gnueabi",
                )
            ),
        }

    def build(self) -> linux.BuildMachine:
        if "xpert-build" in tbot.flags:
            return self
        elif "hercules-build" in tbot.flags:
            return builders.HerculesSSH(self)
        elif "hercules-1604-build" in tbot.flags:
            return builders.Hercules1604SSH(self)
        elif "threadripper-1604-build" in tbot.flags:
            return builders.Threadripper1604SSH(self)
        elif "xmg-build" in tbot.flags:
            return builders.xmgSSH(self)
        raise RuntimeError ("build Machine not specified")

LAB = XpertLab
FLAGS = {
        "revc" : "Use rev c board in xpert lab",
        "nopoweroff" : "Do not power off board at the end",
}
