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
    "u-boot.bin",
    "u-boot.cfg",
    "SPL",
]

@tbot.testcase
def wandboard_check_iperf(
    lab: linux.LinuxShell = None,
    board: board.Board = None,
    blx: linux.LinuxShell = None,
    cycles: str = "5",
    minval: str = "70",
    intervall: str = "5",
) -> bool:
    """
    check networkperformance with iperf
    """
    with contextlib.ExitStack() as cx:
        if lab is not None:
            lh = lab
        else:
            lh = cx.enter_context(tbot.acquire_lab())

        if board is not None:
            b = board
        else:
            b = cx.enter_context(tbot.acquire_board(lh))

        if blx is not None:
            lnx = blx
        else:
            lnx = cx.enter_context(tbot.acquire_linux(b))

        ge.lx_check_iperf(
            lh,
            lnx,
            intervall=intervall,
            cycles=cycles,
            minval=minval,
            filename="iperf.dat",
            showlog=True)

    return True

@tbot.testcase
def wandboard_ub_build(
    lab: typing.Optional[linux.LinuxShell] = None,
) -> None:
    """
    build u-boot
    """
    ge.ub_build("wandboard DL", ub_resfiles)

@tbot.testcase
def wandboard_ub_check_version(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
    """
    check if installed U-Boot version is the same as in
    tftp directory.
    """
    ge.ub_check_version(ub_resfiles)

@tbot.testcase
@tbot.with_uboot
def wandboard_ub_unittest(ub) -> None:
    """
    start u-boot unit test command
    """
    log_event.doc_begin("ub_call_unit_test")
    ub.exec0("ut", "all")
    log_event.doc_end("ub_call_unit_test")

@tbot.testcase
@tbot.with_uboot
def wandboard_ub_interactive(ub) -> None:
    """
    set ub environment and go into interactive console
    """
    ub.do_set_env(ub)
    ub.interactive()

@tbot.testcase
@tbot.with_uboot
def wandboard_ub_install(ub) -> None:
    # and install
    ub.do_set_env(ub)
    ub.exec0("run", "load_spl")
    ub.exec0("run", "upd_spl")
    ub.exec0("run", "cmp_spl")
    ub.exec0("run", "load_ub")
    ub.exec0("run", "upd_ub")
    ub.exec0("run", "cmp_ub")

@tbot.testcase
@tbot.with_uboot
def wandboard_ub_interactive(ub) -> None:
    # and install
    ub.do_set_env(ub)
    ub.interactive()

### Linux
regfile_path = 'tc/wandboard/files/'
reg_file = [
    regfile_path + "wandboard_iomux.reg",
]

@tbot.testcase
def wandboard_ub_build_install_test(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
        wandboard_ub_build()
        wandboard_ub_install()
        wandboard_ub_check_version()
        #wandboard_ub_unittest(ub)
        uboot_testpy()

@tbot.testcase
@tbot.with_linux
def wandboard_lx_check_register(lnx) -> bool:
    """
    check registers on wandboard board. register files
    defined in reg_file
    """
    for f in reg_file:
        ret = ge.lx_check_revfile(lnx, f, "regdifferences_wandboard_lnx")
        if ret == False:
            raise RuntimeError("found register differences")
