import functools
import getpass
import pathlib
import typing
import tbot
from tbot.machine import channel
from tbot.machine.linux import lab
from tbot.machine import linux
import builders

class Tbot2goLab(lab.SSHLabHost, linux.BuildMachine):
    name = "tbot2go"
    hostname = "192.168.1.110"
    username = "pi"
    serverip = "192.168.3.1"
    tftproot = "/srv/tftpboot"
    boardip = {
        "sanvito":   "192.168.3.22",
        "h03pl086":  "192.168.3.32",
        "k30rf":     "192.168.7.37",
        "piinstall": "192.168.1.113",
    }

    @property
    def yocto_result_dir(self) -> "linux.path.Path[Tbot2goLab]":
        return linux.Path(self, f"{self.tftproot}/" + tbot.selectable.Board.name + "/tbot/yocto_results")

    @property
    def workdir(self) -> "linux.path.Path[Tbot2goLab]":
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

    def build(self) -> linux.BuildMachine:
        if "pollux-build" in tbot.flags:
            return builders.PolluxSSH(self)
        elif "xpert-build" in tbot.flags:
            return builders.XpertSSH(self)
        elif "hercules-build" in tbot.flags:
            return builders.HerculesSSH(self)
        elif "hercules-1604-build" in tbot.flags:
            return builders.Hercules1604SSH(self)
        elif "threadripper-build" in tbot.flags:
            return builders.ThreadripperSSH(self)
        elif "threadripper-1604-build" in tbot.flags:
            return builders.Threadripper1604SSH(self)
        elif "xmg-build" in tbot.flags:
            return builders.xmgSSH(self)
        raise RuntimeError ("build Machine not specified")


        return self


LAB = Tbot2goLab
FLAGS = {
        "local-build": "Use Xmglab as buildhost",
        "16mb" : "16 mb version of k30rf board",
        "nopoweroff" : "Do not power off board at the end",
        "gitlabrunner" : "build triggered from gitlabrunner",
        }
