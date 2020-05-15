import functools
import getpass
import pathlib
import typing
import tbot
from tbot.machine import connector, linux, board
import builders
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir + '/tc/commonhelper')
import generic as ge

class Tbot2goLab(connector.SSHConnector, linux.Bash, linux.Lab, linux.Builder):
    hostname = "192.168.1.110"
    username = "hs"
    name = "tbot2go"
    serverip = "192.168.3.1"
    tftproot = "/srv/tftpboot"
    ub_load_board_env_subdir = "tbot"
    boardip = {
        "sanvito":   "192.168.3.22",
        "h03pl086":  "192.168.3.32",
        "k30rf":     "192.168.7.37",
        "piinstall": "192.168.1.113",
        "bbb": "192.168.3.20",
    }

    @property
    def ssh_config(self) -> typing.List[str]:
        """
        if ProxyJump does not work, execute this command from hand
        on the lab PC with BatchMode=no" -> answer allwith "yes"
        If again password question pops up, copy id_rsa.pub from
        lab PC to authorized_keys on build PC
        """
        if "outside" in tbot.flags:
             return ["ProxyJump=pi@xeidos.ddns.net"]
             return ["ProxyJump=pi@xeidos.ddns.net,hs@192.168.1.110"]

        return ""

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath(f"/home/{self.username}/.ssh/id_rsa")
    )

    def set_bootmode(self, state):
        if tbot.selectable.Board.name == "bbb":
            if state == "sd":
                ge.lx_gpio(self, "2", "on")
            elif state == "emmc":
                ge.lx_gpio(self, "2", "off")
            else:
                raise NotImplementedError(f"{state} bootmode defined for {tbot.selectable.Board.name}!")
        else:
            raise NotImplementedError(f"no bootmode defined for {tbot.selectable.Board.name}!")

    @property
    def nfs_root(self) -> "linux.Path[Tbot2goLab]":
        return linux.Path(self, f"/work/tbot2go/tbot/nfs")

    @property
    def tftp_dir(self) -> "linux.path.Path[SmallLab]":
        return linux.Path(self, f"{self.tftproot}/{tbot.selectable.Board.name}/{self.ub_load_board_env_subdir}")

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
        return linux.Path(self, f"{tbot.selectable.Board.name}/{self.ub_load_board_env_subdir}")


    @property
    def yocto_result_dir(self) -> "linux.Path[Tbot2goLab]":
        return linux.Path(self, f"{self.tftproot}/" + tbot.selectable.Board.name + "/tbot/yocto_results")

    @property
    def workdir(self) -> "linux.Path[Tbot2goLab]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot-workdir")

    def init(self):
        ret = self.exec0("ifconfig", "eth0")
        if self.serverip not in ret:
            self.exec0("sudo", "ifconfig", "eth0", "down", self.serverip, "up")

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
        elif "threadripper-1604-kas-build" in tbot.flags:
            return builders.Threadripper1604kasSSH(self)
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
        "outside" : "login not from home",
        }
