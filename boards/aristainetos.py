import typing
import tbot
from tbot.machine import board, channel, linux, connector
from tbot.tc import git

if tbot.selectable.LabHost.name == "pollux":
    # Use pollux specific config
    import pollux as lab

else:
    raise NotImplementedError("Board not available on this labhost!")

class aristainetos(lab.Board):
    name = "aristainetos"
    connect_wait = 2.0
    if "oldversion" in tbot.flags:
        envdir = "aristainetos/20171121/env.txt"
    elif "pollux-build" in tbot.flags:
        envdir = "aristainetos/tbot/env.txt"
    else:
        envdir = "aristainetos/20200302/env.txt"

class aristainetosUBootBuilder(lab.UBootBuilder):
    name = "aristainetos-builder"
    defconfig = "aristainetos2_defconfig"
    toolchain = "arm"
    remote = "git@gitlab.denx.de:u-boot/u-boot.git"

    testpy_boardenv = r"""# Config for aristainetos
# Set sleep time and margin
env__sleep_time = 20
env__sleep_margin = 2
"""


    def do_checkout(self, target: linux.Path, clean: bool, rev: typing.Optional[str]) -> git.GitRepository:
        branch = "master"
        return git.GitRepository(
            target=target, url=self.remote, clean=clean, rev=branch
        )

    def do_patch(self, repo: git.GitRepository) -> None:
        repo.am(linux.Path(repo.host, "/home/hs/abb/mainlining/aristainetos/patches/20200708"))

class aristainetosUBoot(lab.UBootMachine):
    name = "ari-ub"
    prompt = "=> "
    autoboot_prompt = None
    build = aristainetosUBootBuilder()

BOARD = aristainetos
UBOOT = aristainetosUBoot
