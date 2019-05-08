import typing
import tbot
from tbot.machine.linux import lab
from tbot.machine import linux
import builders

class PolluxLab(lab.SSHLabHost, linux.BuildMachine):
    name = "pollux"
    hostname = "pollux.denx.de"
    username = "hs"

    tftproot = "/tftpboot"
    serverip = "192.168.1.1"
    netmask = "255.255.0.0"
    boardip = {}
    boardip["wandboard"] = "192.168.20.62"
    ethaddr = {}
    ethaddr["wandboard"] = "00:1f:7b:b2:00:0f"

    def set_bootmode(self, state):
        if tbot.selectable.Board.name == "aristainetos":
            if state == "sd":
                self.exec0("relais", "relsrv-02-03", "1", "on")
            else:
                self.exec0("relais", "relsrv-02-03", "1", "off")
        else:
            raise NotImplementedError(f"no bootmode defined for {tbot.selectable.Board.name}!")

    @property
    def yocto_result_dir(self) -> "linux.path.Path[Tbot2goLab]":
        return linux.Path(self, f"{self.tftproot}/" + tbot.selectable.Board.name + "/tbot/yocto_results")

    @property
    def get_boardname(self) -> str:
        if tbot.selectable.Board.name == "taurus":
            return "at91_taurus"
        elif tbot.selectable.Board.name == "wandboard":
            return "wandboard_dl"

        return tbot.selectable.Board.name

    @property
    def tftp_dir(self) -> "linux.path.Path[PolluxLab]":
        if tbot.selectable.Board.name == "taurus":
            return linux.Path(self, f"/tftpboot/at91_taurus/tbot/")
        else:
            return linux.Path(self, f"/tftpboot/{self.get_boardname}/tbot")

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

LAB = PolluxLab
