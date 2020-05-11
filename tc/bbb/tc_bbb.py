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
    ge.ub_build("BeagleBoneBlack", ub_resfiles)

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
    ge.ub_check_version(ub_resfiles)

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
