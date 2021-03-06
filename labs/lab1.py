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
from tbot_contrib import utils

class Lab1Lab(connector.SSHConnector, linux.Bash, linux.Lab, linux.Builder):
    name = "lab1"
    hostname = "192.168.1.109"
    username = "hs"

    netmask = "255.255.255.0"
    ethaddr = {}
    ethaddr["wandboard"] = "00:1f:7b:b2:00:0f"

    serverip = {
            "wandboard" : "192.168.3.1",
            "k30rf" : "192.168.7.1",
    }
    tftproot = "/var/lib/tftpboot"
    ub_load_board_env_subdir = "tbot"
    boardip = {
        "k30rf":     "192.168.7.37",
        "wandboard" : "192.168.3.21",
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

        return ""

    @property
    def authenticator(self) -> linux.auth.Authenticator:
        return linux.auth.PrivateKeyAuthenticator(
            pathlib.PurePosixPath(f"/home/{self.username}/.ssh/id_rsa")
    )

    @property
    def tftp_dir(self) -> "linux.path.Path[SmallLab]":
        return linux.Path(self, f"/srv/tftpboot/" + self.get_boardname + "/tbot")

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
        return linux.Path(self, f"{tbot.selectable.Board.name}/tbot")

    @property
    def workdir(self) -> "linux.path.Path[Lab1]":
        return linux.Workdir.static(self, f"/work/{self.username}/tbot-workdir")

    @property
    def toolsdir(self) -> "linux.path.Path[Lab1]":
        return linux.Path(self, "/home/hs/tbot2go/bin")

    @property
    def yocto_result_dir(self) -> "linux.Path[Lab1]":
        return linux.Path(self, f"{self.tftproot}/" + tbot.selectable.Board.name + "/tbot/yocto_results")

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
                host_arch = "x86_64",
                arch = "arm-linux-gnueabi",
                date = "2019.12",
                gcc_vers = "7.5",
                gcc_subvers = "0",
                ),
        }

    def init(self):
        # check if nfs server is running, if not start it
        utils.ensure_sd_unit(self, ["nfs-server.service", "tftp.socket"])

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
        elif "lab-1-build" in tbot.flags:
            return self.clone()
        raise RuntimeError ("build Machine not specified")

LAB = Lab1Lab
