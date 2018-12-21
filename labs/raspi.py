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
            pathlib.PurePosixPath("/home") / "pi" / ".ssh" / "id_rsa"
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
            pathlib.PurePosixPath("/home") / "pi" / ".ssh" / "id_rsa"
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

class PolluxSSH(linux.SSHMachine, linux.BuildMachine):
    name = "pollux"
    hostname = "pollux.denx.org"
    username = "hs"

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath("/home") / "pi" / ".ssh" / "id_rsa"
    )

    @property
    def workdir(self) -> "linux.Path[PolluxSSH]":
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

class XmglapSSH(linux.SSHMachine, linux.BuildMachine):
    name = "xmglap-build"
    username = "hs"
    hostname = "192.168.1.106"
    repo_path = "/home/hs/bin/repo"

    @property
    def workdir(self) -> "linux.Path[XmglapBuild]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot2go")

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath("/home") / "pi" / ".ssh" / "id_rsa"
    )

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

class ThreadripperSSH(linux.SSHMachine, linux.BuildMachine):
    name = "threadripper-build"
    username = "hs"
    hostname = "192.168.1.120"
    dl_dir = "/work/downloads"
    sstate_dir = f"/work/{username}/tbot2go/yocto-sstate"

    @property
    def workdir(self) -> "linux.Path[XmglapBuild]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot2go")

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath("/home") / "pi" / ".ssh" / "id_rsa"
    )

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
        return [f"ProxyJump={self.username}@192.168.1.120"]

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath("/home") / "pi" / ".ssh" / "id_rsa"
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

class Tbot2goLab(lab.SSHLabHost, linux.BuildMachine):
    name = "tbot2go"
    hostname = "192.168.1.110"
    username = "pi"
    serverip = "192.168.3.1"
    boardip = {}
    boardip["sanvito"] = "192.168.3.22"
    boardip["h03pl086"] = "192.168.3.32"
    boardip["k30rf"] = "192.168.7.37"

    @property
    def yocto_result_dir(self) -> "linux.path.Path[Tbot2goLab]":
        return linux.Path(self, f"/srv/tftpboot/" + tbot.selectable.Board.name + "/tbot/yocto_results")

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
            return PolluxSSH(self)
        elif "hercules-build" in tbot.flags:
            return HerculesSSH(self)
        elif "hercules-1604-build" in tbot.flags:
            return Hercules1604SSH(self)
        elif "threadripper-build" in tbot.flags:
            return ThreadripperSSH(self)
        elif "threadripper-1604-build" in tbot.flags:
            return Threadripper1604SSH(self)
        else:
            return XmglapSSH(self)

LAB = Tbot2goLab
FLAGS = {"local-build": "Use Xmglab as buildhost",
        "hercules-build":"Use hercules for build",
        "pollux-build":"Use pollux as buildhost",
        "hercules-1604-build":"build on hercules in ubuntu 16.04 container",
        "threadripper-build":"build on threadripper",
        "threadripper-1604-build":"build on threadripper in ubuntu 16.04 container",
        }
