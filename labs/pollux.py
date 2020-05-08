import typing
import tbot
from tbot.machine import connector, linux, board
import builders

class PolluxLab(connector.ParamikoConnector, linux.Bash, linux.Lab, linux.Builder):
    name = "pollux"
    hostname = "pollux.denx.org"
    username = "hs"

    tftproot = "/tftpboot"
    serverip = "192.168.1.1"
    netmask = "255.255.0.0"
    boardip = {}
    boardip["wandboard"] = "192.168.20.62"
    boardip["aristainetos"] = "192.168.20.75"
    ethaddr = {}
    ethaddr["wandboard"] = "00:1f:7b:b2:00:0f"
    ethaddr["aristainetos"] = "32:8f:5c:26:25:b9"

    def set_bootmode(self, state):
        if tbot.selectable.Board.name == "aristainetos":
            if state == "sd":
                self.exec0("relais", "relsrv-02-03", "1", "on")
            else:
                self.exec0("relais", "relsrv-02-03", "1", "off")
        else:
            raise NotImplementedError(f"no bootmode defined for {tbot.selectable.Board.name}!")

    @property
    def yocto_result_dir(self) -> "linux.Path":
        return linux.Path(self, f"{self.tftproot}/" + tbot.selectable.Board.name + "/tbot/yocto_results")

    @property
    def get_boardname(self) -> str:
        if tbot.selectable.Board.name == "taurus":
            return "at91_taurus"
        elif tbot.selectable.Board.name == "wandboard":
            return "wandboard_dl"

        return tbot.selectable.Board.name

    @property
    def tftp_dir(self) -> "linux.Path[PolluxLab]":
        if tbot.selectable.Board.name == "taurus":
            return linux.Path(self, f"{self.tftproot}/at91_taurus/tbot/")
        else:
            return linux.Path(self, f"{self.tftproot}/{self.get_boardname}/tbot")

    @property
    def tftp_root_path(self) -> "linux.Path[Lab1]":
        """
        returns root tftp path
        """
        return linux.Path(self, self.tftproot)

    @property
    def tftp_dir_board(self) -> "linux.Path[Lab1]":
        """
        returns tftp path for u-boot tftp command
        """
        if tbot.selectable.Board.name == "socrates":
            return linux.Path(self, f"{tbot.selectable.Board.name}-abb/{tbot.selectable.Board.date}")
        else:
            return linux.Path(self, f"{tbot.selectable.Board.name}/tbot")

    @property
    def sign_dir(self) -> "linux.Path[PolluxLab]":
        return linux.Path(self, f"/home/hs/tools/cst-2.3.3/linux64/bin")

    @property
    def workdir(self) -> "linux.Path[PolluxLab]":
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
        }

    def build(self) -> linux.Builder:
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
