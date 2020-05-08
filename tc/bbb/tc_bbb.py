import contextlib
import typing
import tbot
from datetime import datetime
from tbot.machine import board, linux
from tbot.tc import uboot

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir + '/commonhelper')
import generic as ge

from tbot.tc.uboot import build as uboot_build
from tbot import log_event
from tbot.tc.uboot import testpy as uboot_testpy

ub_resfiles = [
    "System.map",
    "u-boot.img",
    "u-boot.cfg",
    "MLO",
]

@tbot.testcase
def bbb_ub_build(
    lab: typing.Optional[linux.LinuxShell] = None,
    build: typing.Optional[linux.LinuxShell] = None,
) -> None:
    """
    build u-boot
    """
    with lab or tbot.acquire_lab() as lh:
        # remove all old source code
        #lh.exec0("rm", "-rf", "/work/hs/tbot-workdir/uboot-wandboard-builder")
        git = uboot_build(lab=lh)

        name = "BeagleBoneBlack" # get this from U-Boot bootlog
        log_event.doc_tag("UBOOT_BOARD_NAME", name)
        today = datetime.now()
        log_event.doc_tag("UBOOT_BUILD_TIME", today.strftime("%Y-%m-%d %H:%M:%S"))
        log_event.doc_tag("UBOOT_BUILD_TITLE", f"tbot automated build of {name}")
        log_event.doc_tag("UBOOT_NOTES", "built with tbot")
        for f in ub_resfiles:
            s = git / f
            r = lh.tftp_root_path / ge.get_path(lh.tftp_dir_board)
            t = r / f
            p = ge.get_path(t)
            tbot.tc.shell.copy(s, t)
            lh.exec0("chmod", "666", t)
            if f == "MLO":
                ret = lh.exec0("ls", "-al", p, linux.Pipe, "cut", "-d", " ", "-f", "5")
                log_event.doc_tag("UBOOT_SPL_SIZE", ret.strip())
            if f == "u-boot.img":
                ret = lh.exec0("ls", "-al", p, linux.Pipe, "cut", "-d", " ", "-f", "5")
                log_event.doc_tag("UBOOT_UBOOT_SIZE", ret.strip())

@tbot.testcase
def bbb_ub_check_version(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
    """
    check if installed U-Boot version is the same as in
    tftp directory.
    """
    with lab or tbot.acquire_lab() as lh:
        r = ge.get_path(lh.tftp_root_path) + "/" + ge.get_path(lh.tftp_dir_board)
        spl_vers = None
        ub_vers = None
        for f in ub_resfiles:
            if "MLO" in f:
                log_event.doc_begin("get_spl_vers")
                spl_vers = lh.exec0(linux.Raw(f'strings {r}/{f} | grep --color=never "U-Boot SPL 2"'))
                spl_vers = spl_vers.strip()
                log_event.doc_tag("ub_spl_new_version", spl_vers)
                log_event.doc_end("get_spl_vers")
                tbot.log.message(tbot.log.c(f"found in image U-Boot SPL version {spl_vers}").green)
            if "u-boot.img" in f:
                log_event.doc_begin("get_ub_vers")
                ub_vers = lh.exec0(linux.Raw(f'strings {r}/{f} | grep --color=never "U-Boot 2"'))
                for l in ub_vers.split('\n'):
                    if ":" in l:
                        ub_vers = l.strip()
                log_event.doc_tag("ub_ub_new_version", ub_vers)
                log_event.doc_end("get_ub_vers")
                tbot.log.message(tbot.log.c(f"found in image U-Boot version {ub_vers}").green)

        with contextlib.ExitStack() as cx:
            if board is not None:
                b = board
            else:
                b = cx.enter_context(tbot.acquire_board(lh))
            if ubx is not None:
                ub = ubx
            else:
                ub = cx.enter_context(tbot.acquire_uboot(b))
            if spl_vers != None:
                if spl_vers not in ub.bootlog:
                    raise RuntimeError(f"{spl_vers} not found.")
                tbot.log.message(tbot.log.c(f"found U-Boot SPL version {spl_vers} installed").green)
            if ub_vers == None:
                raise RuntimeError(f"No U-Boot version defined")
            else:
                if ub_vers not in ub.bootlog:
                    raise RuntimeError(f"{ub_vers} not found.")
                tbot.log.message(tbot.log.c(f"found U-Boot version {ub_vers} installed").green)

@tbot.testcase
@tbot.with_uboot
def bbb_ub_unittest(ub) -> None:
    """
    start u-boot unit test command
    """
    log_event.doc_begin("ub_call_unit_test")
    ub.exec0("ut", "all")
    log_event.doc_end("ub_call_unit_test")

@tbot.testcase
@tbot.with_uboot
def bbb_ub_interactive(ub) -> None:
    """
    set ub environment and go into interactive console
    """
    ub.do_set_env(ub)
    ub.interactive()

@tbot.testcase
@tbot.with_uboot
def bbb_ub_install_sd(ub) -> None:
    # and install
    ub.do_set_env(ub)
    if "bootmodeemmc" in tbot.flags:
        raise RuntimeError("tbot flag bootmodeemmc not supported")

    ub.exec0("run", "load_mlo")
    ub.exec0("run", "upd_mlo")
    ub.exec0("run", "cmp_mlo")
    ub.exec0("run", "load_uboot")
    ub.exec0("run", "upd_uboot")
    ub.exec0("run", "cmp_uboot")

@tbot.testcase
@tbot.with_uboot
def bbb_ub_interactive(ub) -> None:
    # and install
    ub.do_set_env(ub)
    ub.interactive()

@tbot.testcase
def bbb_ub_build_install_test(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
    bbb_ub_build()
    bbb_ub_install_sd()
    bbb_ub_check_version()
    uboot_testpy()
