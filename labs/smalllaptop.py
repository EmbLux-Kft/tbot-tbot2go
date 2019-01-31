import pathlib
import typing
import tbot
from tbot.machine.linux import lab
from tbot.machine import linux

class Threadripper1604SSH(linux.SSHMachine, linux.BuildMachine):
    name = "threadripper-1604-build"
    username = "hs"
    hostname = "192.168.1.120"
    port = 11604
    dl_dir = "/work/downloads"
    sstate_dir = f"/work/{username}/tbot2go/yocto-sstate"

    @property
    def ssh_config(self) -> typing.List[str]:
        return [f"ProxyJump={self.username}@192.168.1.120"]

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath("/home") / "hs" / ".ssh" / "id_rsa"
        )

    @property
    def workdir(self) -> "linux.Path[Threadripper1604SSH]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot2go")

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


class SmalllaptopLab(lab.SSHLabHost, linux.BuildMachine):
    name = "small-lab"
    #hostname = "192.168.1.105"
    hostname = "192.168.3.10"
    username = "hs"

    serverip = "192.168.3.10"
    netmask = "255.255.255.0"
    boardip = {}
    boardip["wandboard"] = "192.168.3.20"
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
        return linux.Path(self, f"/var/lib/tftpboot/{self.get_boardname}/tbot")

    @property
    def tftp_dir_board(self) -> "linux.path.Path[SmallLab]":
        return linux.Path(self, f"{self.get_boardname}/tbot")

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
        if "threadripper-1604-build" in tbot.flags:
            return Threadripper1604SSH(self)
        return self

LAB = SmalllaptopLab
FLAGS = {
        "threadripper-1604-build":"build on threadripper in ubuntu 16.04 container",
        }
