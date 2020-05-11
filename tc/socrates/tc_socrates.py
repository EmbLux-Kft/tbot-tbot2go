import contextlib
import typing
import tbot
from tbot.machine import linux
from tbot.machine import board
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir + '/commonhelper')
import generic as ge
import yocto
import time
from tbot.tc import uboot
from tbot.tc.uboot import build as uboot_build
from tbot import log_event
from datetime import datetime
import bdi
from tbot.tc.uboot import testpy as uboot_testpy

# configs
path = "tc/socrates/files/"

ub_resfiles = [
    "System.map",
    "u-boot-socrates.bin",
]

# da9063
i2c_dump_0_58 = [
        "0x00: 00 00 04 23 00 02 f1 41 04 23 00 10 00 00 03 09",
        "0x10: db 68 05 00 40 66 6d 66 66 dd 46 de 66 ff ff b0",
        "0x20: 01 01 01 01 01 01 00 01 01 01 81 01 00 00 00 00",
        "0x30: 01 00 00 00 24 01 aa 00 00 xx 00 00 00 xx xx 3d",
        "0x40: xx xx 13 07 01 00 00 00 00 01 31 00 xx xx 08 00",
]


bd = bdi.Bdi('bdi3',
            'BDI>', '', '', '', '', '', "bdi3.cfg")

@tbot.testcase
def socrates_ub_bdi_update(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubma: typing.Optional[board.UBootShell] = None,
) -> None:
    with contextlib.ExitStack() as cx:
        if lab is not None:
            lh = lab
        else:
            lh = cx.enter_context(tbot.acquire_lab())

        if board is not None:
            b = board
        else:
            b = cx.enter_context(tbot.acquire_board(lh))

        bd.bdi_connect(lh, b)

        bd.bdi_reset_board()

        bd.exec("era")
        if "restore_old_ub" in tbot.flags:
            bd.exec("prog", "0xfffa0000", f"socrates-abb/{b.date}/socrates-u-boot.bin-voncajus", "BIN")
        else:
            bd.exec("era", "0xfff60000")
            bd.exec("prog", "0xfff60000", f"socrates-abb/{b.date}/u-boot-socrates.bin", "BIN")

        bd.bdi_reset_board_run()
        if ubma is not None:
            ub = ubma
        else:
            ub = cx.enter_context(tbot.acquire_uboot(b))

        ub.interactive()

@tbot.testcase
@tbot.with_uboot
def socrates_ub_interactive(ub) -> None:
    """
    set ub environment and go into interactive console
    """
    ub.do_set_env(ub)
    ub.interactive()

@tbot.testcase
def socrates_ub_build(
    lab: typing.Optional[linux.LinuxShell] = None,
) -> None:
    """
    build u-boot
    """
    ge.ub_build("socrates", ub_resfiles)

@tbot.testcase
def socrates_ub_update_i(
    lab: typing.Optional[linux.LinuxShell] = None,
    uboot: typing.Optional[board.UBootShell] = None,
    interactive = True,
) -> None:
    with contextlib.ExitStack() as cx:
        lh = cx.enter_context(lab or tbot.acquire_lab())
        if uboot is not None:
            ub = uboot
        else:
            b = cx.enter_context(tbot.acquire_board(lh))
            ub = cx.enter_context(tbot.acquire_uboot(b))

        ret = ub.exec("ping", "192.168.1.1")
        while ret[0] != 0:
            ret = ub.exec("ping", "192.168.1.1")

        if "restore_old_ub" in tbot.flags:
            tbot.log.message("restore old U-Boot")
            ub.env("uboot_addr", "FFFA0000")
            ub.env("uboot_file", "socrates-abb/20190627/socrates-u-boot.bin-voncajus")
        else:
            ub.env("uboot_addr", "FFF60000")
            ub.env("uboot_file", f"socrates-abb/{b.date}/u-boot-socrates.bin")
            ub.env("update_uboot", "tftp 110000 ${uboot_file};protect off ${uboot_addr} ffffffff;era ${uboot_addr} ffffffff;cp.b 110000 ${uboot_addr} ${filesize}")

        ub.exec0("printenv")
        ub.exec0("run", "update_uboot")

        if interactive:
            ub.interactive()

@tbot.testcase
def socrates_ub_check_version(
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
            if "u-boot-socrates.bin" in f:
                log_event.doc_begin("get_ub_vers")
                ub_vers = lh.exec0(linux.Raw(f'strings {r}/{f} | grep --color=never "U-Boot 2"'))
                ub_vers = ub_vers.strip()
                if ub_vers[0] == 'V':
                    ub_vers = ub_vers[1:]
                log_event.doc_tag("ub_ub_new_version", ub_vers)
                log_event.doc_end("get_ub_vers")
                tbot.log.message(tbot.log.c(f"found in image U-Boot version {ub_vers}").green)

        if ub_vers == None:
            raise RuntimeError(f"No U-Boot version defined")

        with tbot.acquire_board(lh) as b:
            with tbot.acquire_uboot(b) as ub:
                if ub_vers not in ub.bootlog:
                    raise RuntimeError(f"{ub_vers} not found.")

        tbot.log.message(tbot.log.c(f"found U-Boot version {ub_vers} installed").green)

@tbot.testcase
def socrates_ub_build_install_test(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
        socrates_ub_build()
        socrates_ub_update_i(interactive = False)
        socrates_ub_check_version()
        #wandboard_ub_unittest(ub)
        uboot_testpy()


"""
i2c:

=> i2c bus
Bus 0:  fsl_0
Bus 1:  fsl_1

Bus 0
=> i2c dev 0
Setting bus to 0
=>

=> i2c probe
Valid chip addresses: 0C 28 32 48 49 4C 50 51 69
=>

dtt @28:
=> i2c md 28 0 10
0000: ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff    ................
(sicher falsch)

rtc @ 32
=> i2c md 32 0 10
0000: 09 01 10 04 27 06 19 00 00 00 00 00 00 00 20 20    ....'.........
=>

=> i2c md 48 0 10
0000: 4f 80 ff ff ff ff ff ff ff ff ff ff ff ff ff ff    O...............
=> i2c md 49 0 10
0000: 51 00 ff ff ff ff ff ff ff ff ff ff ff ff ff ff    Q...............
=>

dtt @ 4c
=> i2c md 4c.0 0 10
0000: 2b 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00    +...............
=>

eeprom ?
=> i2c md 50 0 20
0000: 80 08 08 0d 0a a0 40 00 05 30 45 00 82 10 00 00    ......@..0E.....
0010: 0c 08 38 01 04 00 03 3d 50 50 60 3c 28 3c 2d 80    ..8....=PP`<(<-.
=>

Bus 1

=> i2c dev 1
Setting bus to 1
=> i2c probe
Valid chip addresses:
=>

"""

@tbot.testcase
def socrates_ub_usb(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubma: typing.Optional[board.UBootShell] = None,
) -> None:
    """
    start usb and check if there is a usb storage device
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

        if ubma is not None:
            ub = ubma
        else:
            ub = cx.enter_context(tbot.acquire_uboot(b))

        ret = ub.exec0("usb", "start")
        if "1 Storage Device" not in ret:
            raise RuntimeError("no usb storage device found")

        ret = ub.exec0("usb", "storage")
        if "Vendor: Kingston" not in ret:
            raise RuntimeError("vendor not Kingston")
        if "Capacity: 954.0 MB" not in ret:
            raise RuntimeError("wrong Capacity")

        ub.exec0("usb", "read", "100000", "0", "1000")

        ret = ub.exec0("crc", "100000", "80000")
        if "e336ee43" not in ret:
            raise RuntimeError(f"wrong checksum f{ret}")


FLAGS = {
        "restore_old_ub":"restore old U-Boot",
        }
