import typing
import tbot
from tbot.machine import board
from tbot.machine import linux

if tbot.selectable.LabHost.name == "pollux":
    # Use pollux specific config
    import denx

    BoardBase = denx.DenxBoard

    class wandboardUbootBuild(denx.DenxUBootBuildInfo):
        name = "wandboard"
        defconfig = "wandboard_defconfig"
        toolchain = "linaro-gnueabi"
        # how to get here the workdir from the build host ?
        ub_patches_path = None

elif tbot.selectable.LabHost.name == "tbot2go":
    # Use your personal lab config
    import raspi
    
    BoardBase = raspi.Tbot2goBoard

    class wandboardUbootBuild(raspi.Tbot2goUBootBuildInfo):
        name = "wandboard"
        defconfig = "wandboard_defconfig"
        toolchain = "linaro-gnueabi"

elif tbot.selectable.LabHost.name == "embedded-lab":
    # Use Stefano specific config
    import stefano

    BoardBase = stefano.StefanoBoard

    class wandboardUbootBuild(stefano.StefanoUBootBuildInfo):
        name = "wandboard"
        defconfig = "wandboard_defconfig"
        toolchain = "linaro-gnueabi"

elif tbot.selectable.LabHost.name == "small-lab":
    # Use small laptop specific config
    import smalllaptop

    BoardBase = smalllaptop.SmalllaptopBoard

    class wandboardUbootBuild(smalllaptop.SmalllaptopUBootBuildInfo):
        name = "wandboard"
        defconfig = "wandboard_defconfig"
        toolchain = "linaro-gnueabi"

else:
    raise NotImplementedError("Board not available on this labhost!")
    
class wandboard(BoardBase):
    name = "wandboard"
    connect_wait = 0.0

UBOOTBUILD = wandboardUbootBuild

class wandboardUBoot(board.UBootMachine[wandboard]):
    prompt = "=> "
    build = UBOOTBUILD

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
