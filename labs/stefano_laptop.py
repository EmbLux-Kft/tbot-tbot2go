import typing
import tbot
from tbot.machine.linux import lab
from tbot.machine import linux


class HerculesSSH(linux.SSHMachine, linux.BuildMachine):
    name = "hercules"
    hostname = "hercules"

    @property
    def workdir(self) -> "linux.Path[HerculesSSH]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot-workdir")

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


class StefanoLab(lab.SSHLabHost, linux.BuildMachine):
    name = "embedded-lab"
    # oder 192.168.2.177 ?
    hostname = "babic.homelinux.org"
    username = "tbot"
    port = 8122

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
    def tftp_dir(self) -> "linux.path.Path[PolluxLab]":
        return linux.Path(self, f"/srv/tftpboot/" + self.get_boardname + "/tbot")

    @property
    def workdir(self) -> "linux.path.Path[PolluxLab]":
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


LAB = StefanoLab
