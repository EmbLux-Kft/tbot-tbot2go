import functools
import getpass
import pathlib
import typing
import tbot
from tbot.machine import channel
from tbot.machine.linux import lab
from tbot.machine import linux
import builders

class Tbot2goLab2(lab.SSHLabHost, linux.BuildMachine):
    name = "tbot2go2"
    hostname = "192.168.1.115"
    # hostname = "192.168.2.103"
    username = "hs"
    serverip = "192.168.3.1"
    tftproot = "/srv/tftpboot"
    ub_load_board_env_subdir = "tbot"
    boardip = {
        "imx8qxpmek": "192.168.3.20",
    }

    def set_bootmode(self, state):
    	raise NotImplementedError(f"no bootmode defined for {tbot.selectable.Board.name}!")

    @property
    def nfs_root(self) -> "linux.path.Path[Tbot2goLab2]":
        return linux.Path(self, f"/work/tbot2go/tbot/nfs")

    @property
    def yocto_result_dir(self) -> "linux.path.Path[Tbot2goLab2]":
        return linux.Path(self, f"{self.tftproot}/" + tbot.selectable.Board.name + "/tbot/yocto_results")

    @property
    def workdir(self) -> "linux.path.Path[Tbot2goLab2]":
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


LAB = Tbot2goLab2
FLAGS = {
        "local-build": "Use Xmglab as buildhost",
        "nopoweroff" : "Do not power off board at the end",
        "gitlabrunner" : "build triggered from gitlabrunner",
        }
