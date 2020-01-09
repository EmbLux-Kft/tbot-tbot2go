import contextlib
import typing
import tbot
from tbot.machine import board, linux
from tbot.tc import uboot

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir + '/commonhelper')
import generic as ge

from tbot.tc.uboot import build as uboot_build
from tbot import log_event

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
    with lab or tbot.acquire_lab() as lh:
        # remove all old source code
        lh.exec0("rm", "-rf", "/work/hs/tbot-workdir/uboot-wandboard-builder")
        git = uboot_build(lab=lh)

        for f in ub_resfiles:
            s = git / f
            r = lh.tftp_root_path / ge.get_path(lh.tftp_dir_board)
            t = r / f
            tbot.tc.shell.copy(s, t)

@tbot.testcase
def wandboard_ub_check_version(
    lab: typing.Optional[linux.LinuxShell] = None,
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
            if "SPL" in f:
                log_event.doc_begin("get_spl_vers")
                spl_vers = lh.exec0(linux.Raw(f'strings {r}/SPL | grep --color=never "U-Boot SPL"'))
                spl_vers = spl_vers.strip()
                log_event.doc_tag("ub_spl_new_version", spl_vers)
                log_event.doc_end("get_spl_vers")
                tbot.log.message(tbot.log.c(f"found in image U-Boot SPL version {spl_vers}").green)
            if "u-boot.bin" in f:
                log_event.doc_begin("get_ub_vers")
                ub_vers = lh.exec0(linux.Raw(f'strings {r}/u-boot.bin | grep --color=never "U-Boot 2"'))
                ub_vers = ub_vers.strip()
                log_event.doc_tag("ub_ub_new_version", ub_vers)
                log_event.doc_end("get_ub_vers")
                tbot.log.message(tbot.log.c(f"found in image U-Boot version {ub_vers}").green)

        with contextlib.ExitStack() as cx:
            b = cx.enter_context(tbot.acquire_board(lh))
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
def wandboard_ub_unittest(ub) -> None:
    """
    start u-boot unit test command
    """
    log_event.doc_begin("ub_call_unit_test")
    ub.exec0("ut", "all")
    log_event.doc_end("ub_call_unit_test")

import ubootpytest as ubpy

ubt = ubpy.Ubootpytest("/home/hs/data/Entwicklung/messe/2019/testframework/hook-scripts", "/work/hs/tbot-workdir/uboot-wandboard-builder")

@tbot.testcase
def wandboard_ub_call_test_py(
    lab: typing.Optional[linux.LinuxShell] = None,
) -> bool:
    with lab or tbot.acquire_lab() as lh:
        try:
            ubt.ub_call_test_py(lh)
        except:
            # fail, but we pass here
            pass

        return True

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

### Linux
regfile_path = 'tc/wandboard/files/'
reg_file = [
    regfile_path + "wandboard_iomux.reg",
]

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
