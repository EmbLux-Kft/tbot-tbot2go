import typing
import pathlib
import tbot
from tbot.machine import board, channel, linux, connector

class PolluxSSH(connector.SSHConnector, linux.Bash, linux.Builder):
    name = "pollux"
    hostname = "pollux.denx.org"
    username = "hs"
    dl_dir = "/opt/downloads"
    sstate_dir = f"/work/{username}/tbot/yocto-sstate"

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath("/home") / self.username / ".ssh" / "id_rsa"
    )

    @property
    def workdir(self) -> "linux.Path[PolluxSSH]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot")

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
                    "/home/hs/toolchain/linaro/gcc-linaro-7.2.1-2017.11-i686_arm-linux-gnueabi",
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
            "powerpc": linux.build.DistroToolchain("/home/hs/.buildman-toolchains/gcc-7.3.0-nolibc/powerpc-linux/bin", "powerpc", "powerpc-linux-"),
        }

    def do_after_login(self) -> None:
        self.exec0(linux.Raw(f"PATH=/home/{self.username}/bin/repo:$PATH"))
        return None

class Hercules1604SSH(connector.SSHConnector, linux.Bash, linux.Builder):
    name = "hercules-1604"
    hostname = "hercules"
    username = "hs"
    port = 11604
    dl_dir = "/opt/downloads"
    sstate_dir = f"/work/{username}/tbot/yocto-sstate"

    def do_after_login(self) -> None:
        self.exec0(linux.Raw(f"PATH=/home/{self.username}/bin/repo:$PATH"))
        return None

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
        if "gitlabrunner" in tbot.flags:
            return linux.Workdir.static(self, f"/work/{self.username}/tbot2go/gitlab")
        else:
            return linux.Workdir.static(self, f"/work/{self.username}/tbot")

    @property
    def yocto_result_dir(self) -> "linux.path.Path[Hercules1604SSH]":
        return linux.Workdir.static(self, f"/work/hs/tbot/repo/tmp/deploy/images")

    @property
    def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
        return {
            "bootlin-armv5-eabi": linux.build.EnvSetBootlinToolchain(
                arch = "armv5-eabi",
                libc = "glibc",
                typ = "stable",
                date = "2018.11-1",
            ),
        }

class HerculesSSH(connector.SSHConnector, linux.Bash, linux.Builder):
    name = "hercules"
    hostname = "hercules"
    username = "hs"
    dl_dir = "/opt/downloads"
    sstate_dir = f"/work/{username}/tbot/yocto-sstate"

    def do_after_login(self) -> None:
        self.exec0(linux.Raw(f"PATH=/home/{self.username}/bin/repo:$PATH"))
        return None

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
            "bootlin-armv5-eabi": linux.build.EnvSetBootlinToolchain(
                arch = "armv5-eabi",
                libc = "glibc",
                typ = "stable",
                date = "2018.11-1",
            ),
        }

class ThreadripperSSH(connector.SSHConnector, linux.Bash, linux.Builder):
    name = "threadripper-build"
    username = "hs"
    hostname = "192.168.1.120"
    dl_dir = "/work/downloads"
    sstate_dir = f"/work/{username}/tbot2go/yocto-sstate"

    @property
    def workdir(self) -> "linux.Path[XmglapBuild]":
        if "gitlabrunner" in tbot.flags:
            return linux.Workdir.static(self, f"/work/{self.username}/tbot2go/gitlab")
        else:
            return linux.Workdir.static(self, f"/work/{self.username}/tbot2go")

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath("/home") / self.username / ".ssh" / "id_rsa"
    )

    @property
    def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
        return {
            "linaro-gnueabi": linux.build.EnvSetLinaroToolchain(
                host_arch = "x86_64",
                arch = "arm-linux-gnueabi",
                date = "2018.05",
                gcc_vers = "7.3",
                gcc_subvers = "1",
                ),
        }

class Threadripper1604SSH(connector.SSHConnector, linux.Bash, linux.Builder):
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
        #return [f"ProxyJump=pi@xeidos.ddns.net,{self.username}@192.168.1.120"]
        """
        or use this if you have local connection to network
        """
        #return [f"ProxyJump={self.username}@192.168.1.120"]
        return [f""]

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath("/home") / self.username / ".ssh" / "id_rsa"
    )

    @property
    def workdir(self) -> "linux.Path[XmglapBuild]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot2go")

    @property
    def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
        return {
            "bootlin-armv5-eabi": linux.build.EnvSetBootlinToolchain(
                arch = "armv5-eabi",
                libc = "glibc",
                typ = "stable",
                date = "2018.11-1",
            ),
        }

class Threadripper1604kasSSH(connector.SSHConnector, linux.Bash, linux.Builder):
    name = "threadripper-1604-kas-build"
    username = "hs"
    hostname = "192.168.1.120"
    port = 11605
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
        #return [f"ProxyJump=pi@xeidos.ddns.net,{self.username}@192.168.1.120"]
        """
        or use this if you have local connection to network
        """
        #return [f"ProxyJump={self.username}@192.168.1.120"]
        return [f""]

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath("/home") / self.username / ".ssh" / "id_rsa"
    )

    @property
    def workdir(self) -> "linux.Path[XmglapBuild]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot2go")

    @property
    def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
        return {
            "bootlin-armv5-eabi": linux.build.EnvSetBootlinToolchain(
                arch = "armv5-eabi",
                libc = "glibc",
                typ = "stable",
                date = "2018.11-1",
            ),
        }


class XmglapSSH(connector.SSHConnector, linux.Bash, linux.Builder):
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
            "bootlin-armv5-eabi": linux.build.EnvSetBootlinToolchain(
                arch = "armv5-eabi",
                libc = "glibc",
                typ = "stable",
                date = "2018.11-1",
            ),
        }

class XpertSSH(connector.SSHConnector, linux.Bash, linux.Builder):
    name = "xpert-build"
    hostname = "xpert.denx.de"
    username = "hs"
    dl_dir = "/opt/eldk/downloads"
    sstate_dir = f"/work/{username}/tbot-workdir/yocto-sstate"

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath(f"/home/{self.username}/.ssh/id_rsa")
    )

    @property
    def workdir(self) -> "linux.Path[XpertSSH]":
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

class xmgSSH(connector.SSHConnector, linux.Bash, linux.Builder):
    name = "xmg-build"
    username = "hs"
    hostname = "192.168.1.106"
    dl_dir = "/work/downloads"
    sstate_dir = f"/work/{username}/tbot2go/yocto-sstate"

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

FLAGS = {
        "xmg-build" : "build on XMG laptop",
        "pollux-build":"Use pollux as buildhost",
        "xpert-build" : "build on xpert",
        "hercules-build":"Use hercules for build",
        "hercules-1604-build":"build on hercules in ubuntu 16.04 container",
        "threadripper-build":"build on threadripper",
        "threadripper-1604-build":"build on threadripper in ubuntu 16.04 container",
        "threadripper-1604-kas-build":"build on threadripper in ubuntu 16.04 container with kas tool",
}
