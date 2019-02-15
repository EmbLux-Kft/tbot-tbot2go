import typing
import tbot
from tbot.machine import board
from tbot.machine import linux
from tbot.tc import uboot
from tbot.tc import git

if tbot.selectable.LabHost.name == "pollux":
    # Use pollux specific config
    import denx

    BoardBase = denx.DenxBoard

elif tbot.selectable.LabHost.name == "tbot2go":
    # Use your personal lab config
    import raspi
    
    BoardBase = raspi.Tbot2goBoard

elif tbot.selectable.LabHost.name == "embedded-lab":
    # Use Stefano specific config
    import stefano

    BoardBase = stefano.StefanoBoard

elif tbot.selectable.LabHost.name == "small-lab":
    # Use small laptop specific config
    import smalllaptop

    BoardBase = smalllaptop.SmalllaptopBoard
    tbot.selectable.ub_patches = "yes"
    tbot.selectable.ub_patches_path = None

    class WandboardUBootBuilder(uboot.UBootBuilder):
        name = "wandboard-builder"
        defconfig = "wandboard_defconfig"
        toolchain = "linaro-gnueabi"
        remote = "/home/hs/data/Entwicklung/sources/u-boot"

        def do_patch(self, repo: git.GitRepository) -> None:
            log_event.doc_tag("ub_build_cfg_ub_patches", tbot.selectable.ub_patches_path)
            log_event.doc_begin("ub_build_patch")
            repo.am(linux.Path(repo.host, tbot.selectable.ub_patches_path))
            log_event.doc_begin("ub_build_patch_end")
else:
    raise NotImplementedError("Board not available on this labhost!")
    
class wandboard(BoardBase):
    name = "wandboard"
    connect_wait = 0.0

class wandboardUBoot(board.UBootMachine[wandboard]):
    prompt = "=> "
    build = WandboardUBootBuilder()

class wandboardLinux(board.LinuxWithUBootMachine[wandboard]):
    uboot = wandboardUBoot
    username = "debian"
    password = "temppwd"

    shell = linux.shell.Bash

    def do_boot(
        self, ub: board.UBootMachine[wandboard]
    ) -> typing.List[typing.Union[str, board.Special]]:

        #ub.exec0("setenv", "serverip", "192.168.3.1")
        return ["run", "bootcmd"]

BOARD = wandboard
UBOOT = wandboardUBoot
LINUX = wandboardLinux
from tbot import log_event
log_event.doc_tag("board_name", BOARD.name)
log_event.doc_tag("ub_prompt", UBOOT.prompt)
log_event.doc_begin("ub_abstract")
log_event.doc_end("ub_abstract")
