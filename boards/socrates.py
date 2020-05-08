import typing
import tbot
from tbot.machine import channel, board, linux
from tbot.tc import git

if tbot.selectable.LabHost.name == "pollux":
    # Use pollux specific config
    import pollux as lab
else:
    raise NotImplementedError("Board not available on this labhost!")

ub_env = [
    {"name" : "netdev", "val" : "eth0"},
]

class socrates(lab.Board):
    name = "socrates"
    connect_wait = 2.0
    date = "20200508"

class socratesUBootBuilder(lab.UBootBuilder):
    name = "socrates-builder"
    defconfig = "socrates_defconfig"
    toolchain = "powerpc"
    remote = "git@gitlab.denx.de:u-boot/u-boot.git"

    def do_checkout(self, target: linux.Path, clean: bool, rev: typing.Optional[str]) -> git.GitRepository:
        branch = "master"
        return git.GitRepository(
            target=target, url=self.remote, clean=clean, rev=branch
        )

    def do_patch(self, repo: git.GitRepository) -> None:
        repo.am(linux.Path(repo.host, "/home/hs/abb/mainlining/socrates/patches/20200508"))

class socratesUBoot(lab.UBootMachine):
    name = "soc-ub"
    prompt = "=> "
    autoboot_prompt = None
    build = socratesUBootBuilder()

    def do_set_env(
        self, ub: board.UBootShell
    ) -> bool:
        ub.env("serverip", tbot.selectable.LabHost.serverip["socrates"])
        ub.env("netmask", "255.255.255.0")
        ub.env("ipaddr", tbot.selectable.LabHost.boardip["socrates"])

        for env in ub_env:
            ub.env(env["name"], env["val"])


BOARD = socrates
UBOOT = socratesUBoot
from tbot import log_event
log_event.doc_tag("board_name", BOARD.name)
log_event.doc_tag("ub_prompt", UBOOT.prompt)
