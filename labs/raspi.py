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

class PolluxLab(lab.SSHLabHost, linux.BuildMachine):
    name = "pollux"
    hostname = "pollux.denx.de"

    @property
    def workdir(self) -> "linux.path.Path[PolluxLab]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot-workdir")

    @property
    def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
        return {
            "generic-armv5te": linux.build.EnvScriptToolchain(
                linux.Path(
                    self,
                    "/opt/yocto-2.4/generic-armv5te/environment-setup-armv5e-poky-linux-gnueabi",
                )
            ),
            "generic-armv6": linux.build.EnvScriptToolchain(
                linux.Path(
                    self,
                    "/opt/yocto-2.4/generic-armv6/environment-setup-armv6-vfp-poky-linux-gnueabi",
                )
            ),
            "generic-armv7a": linux.build.EnvScriptToolchain(
                linux.Path(
                    self,
                    "/opt/yocto-2.4/generic-armv7a/environment-setup-armv7a-neon-poky-linux-gnueabi",
                )
            ),
            "generic-armv7a-hf": linux.build.EnvScriptToolchain(
                linux.Path(
                    self,
                    "/opt/yocto-2.4/generic-armv7a-hf/environment-setup-armv7ahf-neon-poky-linux-gnueabi",
                )
            ),
            "generic-powerpc-e500v2": linux.build.EnvScriptToolchain(
                linux.Path(
                    self,
                    "/opt/yocto-2.4/generic-powerpc-e500v2/environment-setup-ppce500v2-poky-linux-gnuspe",
                )
            ),
        }

class XmglapSSH(linux.SSHMachine, linux.BuildMachine):
    name = "xmglap-build"
    username = "hs"
    hostname = "192.168.1.106"

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

class Tbot2goLab(lab.SSHLabHost, linux.BuildMachine):
    name = "tbot2go"
    hostname = "192.168.1.110"
    username = "pi"

    @property
    def yocto_result_dir(self) -> "linux.path.Path[Tbot2goLab]":
        return linux.Workdir.static(self, f"/srv/tftpboot/" + tbot.selectable.Board.name + "/tbot/yocto_results")

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
        else:
            return XmglapSSH(self)

LAB = Tbot2goLab
FLAGS = {"local-build": "Use Xmglab as buildhost", "hercules-build":"Use hercules for build", "pollux-build":"Use pollux as buildhost", "hercules-1604-build":"build on hercules in ubuntu 16.04 container"}
