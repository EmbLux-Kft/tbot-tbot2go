import functools
import getpass
import pathlib
import typing
import tbot
from tbot.machine import channel
from tbot.machine.linux import lab
from tbot.machine import linux

class Hercules1604SSH(linux.SSHMachine, linux.BuildMachine):
    name = "hercules-1604"
    hostname = "hercules"
    username = "hs"
    port = 11604

    @property
    def ssh_config(self) -> typing.List[str]:
        return [f"ProxyJump={self.username}@pollux.denx.org,hs@hercules"]

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath(f"/home/{self.username}/.ssh/id_rsa")
    )

    @property
    def workdir(self) -> "linux.Path[HerculesSSH]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot")

    @property
    def yocto_result_dir(self) -> "linux.path.Path[Hercules1604SSH]":
        # HACK, ToDo
        return linux.Workdir.static(self, f"/work/hs/tbot/h03pl086/repo/cuby/build_h03pl086/tmp/deploy/images/h03pl086")
        #return linux.Workdir.static(self, f"/work/tbot2go/tbot/repo-cuby/source/build_h03pl086_ubuntu1604/tmp/deploy/images/h03pl086")

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


class HerculesSSH(linux.SSHMachine, linux.BuildMachine):
    name = "hercules"
    hostname = "hercules"
    username = "hs"

    @property
    def ssh_config(self) -> typing.List[str]:
        return [f"ProxyJump={self.username}@pollux.denx.org"]

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath(f"/home/{self.username}/.ssh/id_rsa")
    )

    @property
    def workdir(self) -> "linux.Path[HerculesSSH]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot")

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

class Threadripper1604SSH(linux.SSHMachine, linux.BuildMachine):
    name = "threadripper-1604-build"
    username = "hs"
    hostname = "192.168.1.120"
    port = 11604
    dl_dir = "/work/downloads"
    sstate_dir = f"/work/{username}/tbot2go/yocto-sstate"

    @property
    def ssh_config(self) -> typing.List[str]:
        """
        if ProxyJump does not work, execute this command from hand
        on the lab PC with BatchMode=no" -> answer allwith "yes"
        If again password question pops up, copy id_rsa.pub from
        lab PC to authorized_keys on build PC
        """
        return [f"ProxyJump=pi@xeidos.ddns.net,{self.username}@192.168.1.120"]

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath("/home") / "hs" / ".ssh" / "id_rsa"
    )

    @property
    def workdir(self) -> "linux.Path[XmglapBuild]":
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

class XpertLab(lab.SSHLabHost, linux.BuildMachine):
    name = "xpert"
    hostname = "xpert.denx.de"
    username = "hs"

    serverip = "192.168.0.4"
    netmask = "255.255.128.0"
    boardip = {}
    boardip["sanvito"] = "192.168.1.11"
    boardip["sanvito-b"] = "192.168.1.12"
    ethaddr = {}
    ethaddr["sanvito"] = "1e:a7:65:aa:71:59"

    @property
    def yocto_result_dir(self) -> "linux.path.Path[XpertLab]":
        return linux.Path(self, f"/srv/tftpboot/" + tbot.selectable.Board.name + "/tbot/yocto_results")

    @property
    def workdir(self) -> "linux.path.Path[XpertLab]":
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
        if "xpert-build" in tbot.flags:
            return XpertSSH(self)
        elif "hercules-build" in tbot.flags:
            return HerculesSSH(self)
        elif "hercules-1604-build" in tbot.flags:
            return Hercules1604SSH(self)
        elif "threadripper-1604-build" in tbot.flags:
            return Threadripper1604SSH(self)
        raise RuntimeError ("build Machine not specified")

LAB = XpertLab
FLAGS = {
        "hercules-build":"Use hercules for build",
        "pollux-build":"Use pollux as buildhost",
        "hercules-1604-build":"build on hercules in ubuntu 16.04 container",
        "threadripper-1604-build":"build on threadripper in ubuntu 16.04 container",
        "revc" : "Use rev c board in xpert lab",
        "nopoweroff" : "Do not power off board at the end",
}
