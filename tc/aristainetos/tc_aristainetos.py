import contextlib
import typing
import tbot
from tbot.machine import board, linux
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir + '/commonhelper')
import generic as ge
import yocto
import time
from tbot.tc import uboot, git
from tbot.tc.uboot import testpy as uboot_testpy

# configs
path = "tc/aristainetos/files/"

# da9063
i2c_dump_0_58_7 = [
        "0x00: 00 00 04 23 00 02 f1 41 04 23 00 10 00 00 03 09",
        "0x10: db 68 05 00 40 66 6d 66 66 dd 46 de 66 ff ff b0",
        "0x20: 01 01 01 01 01 01 00 01 01 01 81 01 00 00 00 00",
        "0x30: 01 00 00 00 24 01 aa 00 00 xx 00 00 00 xx xx 3d",
        "0x40: xx xx xx xx 01 00 00 00 00 01 31 00 xx xx xx 00",
]
i2c_dump_0_58_4 = [
        "0x00: 01 00 04 23 00 02 f1 61 04 23 00 10 00 00 03 09",
        "0x10: db 68 05 00 40 66 6d 66 66 dd 46 de 66 ff ff b0",
        "0x20: 01 01 01 01 01 01 00 01 01 01 81 01 00 00 00 00",
        "0x30: 01 00 00 00 24 01 aa 00 00 xx 00 00 00 xx xx 3d",
        "0x40: xx xx xx xx 01 00 00 00 00 01 31 00 xx xx xx 00",
]


result_files = [
    "u-boot-dtb.imx",
]

# tmp103@0x71
# not used in u-boot

# functions
@tbot.testcase
@tbot.with_uboot
def ari_ub_check_ping(ub) -> None:
    ub.exec0("ping", ub.host.serverip)
    ret = ub.exec("dhcp")
    ret = ub.exec("ping", ub.host.serverip)
    ret = ub.exec("ping", ub.host.serverip)
    ub.interactive()


def check_panel(ub, panel):
    if "lg4573" in panel:
        if not "Dual Lite Board 4" in ub.bootlog:
            raise RuntimeError(f"{panel} should boot with Dual Lite Board 4")
    if "lb07wv8" in panel:
        if not "Dual Lite Board 7" in ub.bootlog:
            raise RuntimeError(f"{panel} should boot with Dual Lite Board 7")

def switch_panel(ub, panel):
    if "lg4573" in panel:
        ub.env("panel", "lb07wv8")
        ub.exec0("saveenv")
        return "lb07wv8"
    else:
        ub.env("panel", "lg4573")
        ub.exec0("saveenv")
        return "lg4573"

@tbot.testcase
@tbot.with_lab
def ari_ub_check_multi_dtb_select(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
    with lab or tbot.acquire_lab() as lh:
        with contextlib.ExitStack() as bx:
            b = bx.enter_context(tbot.acquire_board(lh))
            with contextlib.ExitStack() as cx:
                ub = cx.enter_context(tbot.acquire_uboot(b))

                cur_panel = ge.ub_get_var(ub, "panel")
                old_panel = cur_panel
                check_panel(ub, cur_panel)
                cur_panel = switch_panel(ub, cur_panel)
                ub.ch.sendline("res")

            with contextlib.ExitStack() as cx:
                ub = cx.enter_context(tbot.acquire_uboot(b))
                cur_panel = ge.ub_get_var(ub, "panel")
                if old_panel == cur_panel:
                    raise RuntimeError(f"{cur_panel} == {old_panel}, should change")
                old_panel = cur_panel
                check_panel(ub, cur_panel)
                cur_panel = switch_panel(ub, cur_panel)
                ub.ch.sendline("res")

            with contextlib.ExitStack() as cx:
                ub = cx.enter_context(tbot.acquire_uboot(b))
                cur_panel = ge.ub_get_var(ub, "panel")
                if old_panel == cur_panel:
                    raise RuntimeError(f"{cur_panel} == {old_panel}, should change")
                check_panel(ub, cur_panel)

@tbot.testcase
@tbot.with_lab
def ari_ub_check_empty_environment(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
    """
    check if u-boot works with empty environment
    """
    with lab or tbot.acquire_lab() as lh:
        with contextlib.ExitStack() as bx:
            b = bx.enter_context(tbot.acquire_board(lh))
            with contextlib.ExitStack() as cx:
                ub = cx.enter_context(tbot.acquire_uboot(b))

                if "Dual Lite Board 4" in ub.bootlog:
                    altpanelstr = "lb07wv8"
                    panelstr = "lg4573"
                elif "Dual Lite Board 7" in ub.bootlog:
                    altpanelstr = "lg4573"
                    panelstr = "lb07wv8"
                else:
                    tbot.log.message(tbot.log.c("should boot with Dual Lite Board 4 or 7").green)
                    return

                # delete env -> must boot with default Board 7
                ub.exec0("sf", "probe")
                ub.exec0("sf", "erase", "env", "10000")
                ub.exec0("sf", "erase", "env-red", "10000")
                ub.ch.sendline("res")

            with contextlib.ExitStack() as cx:
                ub = cx.enter_context(tbot.acquire_uboot(b))
                if not "Dual Lite Board 7" in ub.bootlog:
                    raise RuntimeError("should boot with Dual Lite Board 7")
                if not "bad CRC" in ub.bootlog:
                    raise RuntimeError("should boot with bad CRC")

                ub.env("ethaddr", "00:30:D6:10:B8:9D")
                # config alt panel
                ub.env("panel", altpanelstr)
                ret = ub.exec0("saveenv")
                if not "Saving Environment to SPI Flash" in ret:
                    raise RuntimeError(f"Error saving Environment")

                ub.ch.sendline("res")

            # check bootet with alt panel
            with contextlib.ExitStack() as cx:
                ub = cx.enter_context(tbot.acquire_uboot(b))
                if  "bad CRC" in ub.bootlog:
                    raise RuntimeError("should not boot with bad CRC")
                if "lb07wv8" in altpanelstr:
                    if not "Dual Lite Board 7" in ub.bootlog:
                        raise RuntimeError("should boot with Dual Lite Board 7")
                else:
                    if not "Dual Lite Board 4" in ub.bootlog:
                        raise RuntimeError("should boot with Dual Lite Board 4")
                if not "Loading Environment from SPI Flash" in ub.bootlog:
                    raise RuntimeError("board does not load Environment")

                # config panel
                ub.env("panel", panelstr)
                ret = ub.exec0("saveenv")
                if not "Saving Environment to SPI Flash" in ret:
                    raise RuntimeError(f"Error saving Environment")

                ub.ch.sendline("res")

            # check bootet with panel
            with contextlib.ExitStack() as cx:
                ub = cx.enter_context(tbot.acquire_uboot(b))
                if  "bad CRC" in ub.bootlog:
                    raise RuntimeError("should not boot with bad CRC")
                if "lb07wv8" in panelstr:
                    if not "Dual Lite Board 7" in ub.bootlog:
                        raise RuntimeError("should boot with Dual Lite Board 7")
                else:
                    if not "Dual Lite Board 4" in ub.bootlog:
                        raise RuntimeError("should boot with Dual Lite Board 4")

@tbot.testcase
@tbot.with_uboot
def ari_ub_check_bootlog(ub) -> None:
    """
    u-boot check bootlog
    """
    if "U-Boot" not in ub.bootlog:
        raise RuntimeError("missing U-Boot banner")
    if "Started with servicing" not in ub.bootlog:
        raise RuntimeError("missing WDT")
 
@tbot.testcase
@tbot.with_uboot
def ari_ub_set_env(ub) -> None:
    """
    u-boot set environment variables
    """
    ub.env("disable_giga", "yes")
    ub.env("serverip", ub.host.serverip)
    ub.env("netmask", ub.host.netmask)
    ub.env("ipaddr", ub.host.boardip["aristainetos"])
    ub.env("ethaddr", ub.host.ethaddr["aristainetos"])

@tbot.testcase
@tbot.with_uboot
def ari_ub_prepare_nfs_boot(ub) -> None:
    """
    u-boot set environment variables
    """
    ari_ub_set_env(ub)
    ub.env("subdir", "20151010")
    ub.exec0(linux.Raw("setenv get_env_ub mw \${loadaddr} 0x00000000 0x20000\;tftp \${loadaddr} /tftpboot/aristainetos/\${subdir}/env.txt\;env import -t \${loadaddr}"))
    ub.exec0("run", "get_env_ub")
    ub.interactive()


def check_bit_set(val, bit):
    nr = int(val, 16)
    bith = int(bit, 16)
    if not nr & bith:
        return False

    return True

def check_bit_set_i2c_cmd(val, bit):
    val = val.split(" ")
    if check_bit_set(val[1], bit) == False:
        raise RuntimeError(f"bit {bit} not set in 0x{val[1]}")

def check_bit_notset_i2c_cmd(val, bit):
    val = val.split(" ")
    check_bit_set(val[1], bit)
    if check_bit_set(val[1], bit) == True:
        raise RuntimeError(f"bit {bit} set in 0x{val[1]}")

def check_led(ub, name, goodstate):
    val = ub.exec0("led", "list")
    for l in val.split("\n"):
        if name in l:
            if goodstate not in l:
                raise RuntimeError(f"{name} led must be in {goodstate} state")

@tbot.testcase
@tbot.with_uboot
def ari_ub_check_led(ub) -> None:
    """
    u-boot check led and gpio
    """
    # first get gpio 60 state
    ret = ub.exec0("gpio", "status")
    if "GPIO2_28: output: 0" in ret:
        raise RuntimeError("after reset, gpio 60 must be one")

    ub.exec0("led", "led_red", "on")
    ret = ub.exec0("gpio", "status")
    if "GPIO2_28: output: 1" in ret:
        raise RuntimeError("now gpio 60 must be 0")

    ub.exec0("led", "led_red", "off")
    ret = ub.exec0("gpio", "status")
    if "GPIO2_28: output: 0" in ret:
        raise RuntimeError("now gpio 60 must be 1")

    ret = ub.exec0("gpio", "clear", "60")
    if "Warning" in ret:
        raise RuntimeError("gpio state not readable")

    ret = ub.exec0("gpio", "status")
    if "GPIO2_28: output: 1" in ret:
        raise RuntimeError("now gpio 60 must be 1")

    ret = ub.exec("gpio", "set", "60")
    if "Warning" in ret:
        raise RuntimeError("gpio state not readable")

    ret = ub.exec0("gpio", "status")
    if "GPIO2_28: output: 0" in ret:
        raise RuntimeError("now gpio 60 must be 0")

    # check dummy led on ioexpander
    ioxfound = False
    ret = ub.exec0("led", "list")
    for l in ret.split("\n"):
        if "iox" in l:
            ioxfound = True
            if "inactive" in l:
                raise RuntimeError("iox led is inactive, not allowed")
            if "off" not in l:
                raise RuntimeError("iox led must be in off state")
    if ioxfound:
        ub.exec0("i2c", "dev", "2")
        ret = ub.exec0("i2c", "md", "20", "0.1", "1")
        check_bit_set_i2c_cmd(ret, "0x10")

        ub.exec0("led", "iox", "on")
        check_led(ub, "iox", "on")

        ret = ub.exec0("i2c", "md", "20", "0.1", "1")
        check_bit_notset_i2c_cmd(ret, "0x10")

        ub.exec0("led", "iox", "off")
        check_led(ub, "iox", "off")

        ret = ub.exec0("i2c", "md", "20", "0.1", "1")
        check_bit_set_i2c_cmd(ret, "0x10")

from tbot.tc.uboot import build as uboot_build  # noqa

@tbot.testcase
def ari_ub_sign(
    lab: typing.Optional[linux.LinuxShell] = None,
) -> None:
    """
    sign u-boot
    """
    with lab or tbot.acquire_lab() as lh:
        for f in result_files:
            if "u-boot" in f:
                # copy file to sign path
                s = lh.tftp_dir / f
                t = lh.sign_dir / f
                tbot.tc.shell.copy(s, t)
                lh.exec0("cd", lh.sign_dir)
                lh.exec0("pwd")
                lh.exec0("./cst", "--o", "u-boot-dtb_csf.bin", "--i", "u-boot-dtb.csf")
                lh.exec0(linux.Raw("cat u-boot-dtb.imx u-boot-dtb_csf.bin > u-boot-dtb.imx.signed"))
                s = lh.sign_dir / "u-boot-dtb.imx.signed"
                t = lh.tftp_dir / "u-boot-dtb.imx.signed"
                tbot.tc.shell.copy(s, t)
                # cleanup
                lh.exec0("rm", "u-boot-dtb_csf.bin")
                lh.exec0("rm", "u-boot-dtb.imx.signed")
 
@tbot.testcase
def ari_ub_build(
    lab: typing.Optional[linux.LinuxShell] = None,
) -> None:
    """
    build u-boot, sign it and install it on target
    """
    with lab or tbot.acquire_lab() as lh:
        # remove all old source code
        lh.exec0("rm", "-rf", "/work/hs/tbot/uboot-aristainetos")
        git = uboot_build(lab=lh)

        for f in result_files:
            s = git / f
            t = lh.tftp_dir / f
            tbot.tc.shell.copy(s, t)

        ari_ub_sign(lh)

        ari_ub_update(lh)

@tbot.testcase
def ari_ub_check_version(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
    """
    u-boot check if version on board is the same as in binary
    """
    with lab or tbot.acquire_lab() as lh:
        with contextlib.ExitStack() as cx:
            if board is not None:
                b = board
            else:
                b = cx.enter_context(tbot.acquire_board(lh))

            if ubx is not None:
                ub = ubx
            else:
                ub = cx.enter_context(tbot.acquire_uboot(b))

            t = lh.tftp_dir / "u-boot-dtb.imx.signed"

            #bin_vers = lh.exec0("strings", t, linux.Pipe, "grep", '"U-Boot 2"')
            bin_vers = lh.exec0(linux.Raw(f"strings /tftpboot/aristainetos/tbot/u-boot-dtb.imx.signed | grep --color=never 'U-Boot 2'"))
            ub_vers = ub.exec0("version")

            if bin_vers in ub_vers:
                tbot.log.message(tbot.log.c("Info: U-Boot version is the same").green)
            else:
                raise RuntimeError(f"{bin_vers} != {ub_vers}")

@tbot.testcase
def ari_ub_check_hab(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
    """
    u-boot check hab_auth works as expected
    """
    with lab or tbot.acquire_lab() as lh:
        with contextlib.ExitStack() as cx:
            if board is not None:
                b = board
            else:
                b = cx.enter_context(tbot.acquire_board(lh))

            if ubx is not None:
                ub = ubx
            else:
                ub = cx.enter_context(tbot.acquire_uboot(b))

            load_addr = "10000000"
            t = lh.tftp_dir / "testhabfile-pad-ivt.bin.signed"
            ub.exec0("tftp", load_addr, ge.get_ub_tftp_path(lh, t))
            ret = ub.exec0("hab_auth_img", load_addr, linux.special.Raw("${filesize}"))
            if "No HAB Events Found" in ret:
                tbot.log.message(tbot.log.c("Info: no HAB events.").green)
            else:
                raise RuntimeError("HAB events found")

            t = lh.tftp_dir / "boot-pad-ivt.scr.bin.signed"
            ub.exec0("tftp", load_addr, ge.get_ub_tftp_path(lh, t))
            ret = ub.exec0("hab_auth_img", load_addr, linux.special.Raw("${filesize}"))
            if "No HAB Events Found" in ret:
                tbot.log.message(tbot.log.c("Info: no HAB events.").green)
            else:
                raise RuntimeError("HAB events found")

            t = lh.tftp_dir / "testhabfile-pad-ivt.bin.signed.error"
            ub.exec0("tftp", load_addr, ge.get_ub_tftp_path(lh, t))
            ret = ub.exec0("hab_auth_img", load_addr, linux.special.Raw("${filesize}"))
            if "HAB_FAILURE" in ret:
                tbot.log.message(tbot.log.c("Info: HAB events, expected!").green)
            else:
                raise RuntimeError("HAB events not found")

@tbot.testcase
def ari_ub_basic_checks(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
    """
    u-boot check basic stuff
    """
    with lab or tbot.acquire_lab() as lh:
        with contextlib.ExitStack() as cx:
            if board is not None:
                b = board
            else:
                b = cx.enter_context(tbot.acquire_board(lh))

            if ubx is not None:
                ub = ubx
            else:
                ub = cx.enter_context(tbot.acquire_uboot(b))

            ari_ub_set_env(ub)
            ari_ub_check_bootlog(ub)

            # check version
            ari_ub_check_version(lh, b, ub)
            # ethernet works?
            ub.exec0("ping", lh.serverip)
            # mmc work
            ub.exec0("mmc", "info")
            # check led / gpio
            ari_ub_check_led(ub)
            # check i2c
            ari_ub_check_i2c(lh, b, ub)
            # check hab_auth_img command
            ari_ub_check_hab(lh, b, ub)

    # must start from scratch
    # check multi dtb select
    ari_ub_check_multi_dtb_select()
    ari_ub_check_empty_environment()

@tbot.testcase
def ari_ub_update(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
    """
    update u-boot
    """
    with lab or tbot.acquire_lab() as lh:
        # now we know what we have normally as bootmode
        # we want to update this bootmode with new U-Boot
        # so delete bootmode in flags and set other bootmode
        if "bootmodesd" in tbot.flags:
            bm = "sd"
            tbot.flags.remove("bootmodesd")
            lh.set_bootmode("spi")
        elif "bootmodespi" in tbot.flags:
            bm = "spi"
            tbot.flags.remove("bootmodespi")
            lh.set_bootmode("sd")
        else:
            raise RuntimeError("Set bootmode")

        with contextlib.ExitStack() as cx:
            if board is not None:
                b = board
            else:
                b = cx.enter_context(tbot.acquire_board(lh))

            if ubx is not None:
                ub = ubx
            else:
                ub = cx.enter_context(tbot.acquire_uboot(b))

            ari_ub_set_env(ub)
            loadaddr = "0x12000000"
            ret = ub.exec("ping", "192.168.1.1")
            while ret[0] != 0:
                ret = ub.exec("ping", "192.168.1.1")
            ub.exec0("mw", loadaddr, "0", "0x4000")
            ub.exec0("tftp", loadaddr, b.envdir)
            ub.exec0("env", "import", "-t", loadaddr)
            if bm == "sd":
                ub.exec0("run", "upd_uboot_sd")
            else:
                ub.exec0("run", "upd_uboot")

    return

@tbot.testcase
def ari_ub_update_i(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
    interactive = True,
) -> None:
    """
    update U-Boot and go into interactive U-Boot shell
    """
    with lab or tbot.acquire_lab() as lh:
        ari_ub_update(lh, board, ubx)

        lh.set_bootmode("sd")
        with contextlib.ExitStack() as cx:
            if board is not None:
                b = board
            else:
                b = cx.enter_context(tbot.acquire_board(lh))

            b.poweroff()
            time.sleep(5)
            b.poweron()
            if ubx is not None:
                ub = ubx
            else:
                ub = cx.enter_context(tbot.acquire_uboot(b))

            # try to get fb address
            """
            if "Framebuffer at" in ub.bootlog:
                line = ub.bootlog.split("Framebuffer at ")
                #line = line[1].split["\n"]
                #print (line[0])
                addr = line[1]
                if "\n" in addr:
                    addr = addr.split("\n")[0]
            else:
                ret = ub.exec0("bdinfo")
                line = ret.split("FB base     = ")
                addr = line[1]
                addr = addr.split("\n")
                addr = addr[0].strip()

            #ub.exec0("mw", "4fb5c000", "f79e3206", "10000")
            #
            # all white
            #ge.ub_set_mem_addr(ub, addr, "l", "ffffffff", "100000")
            #
            # dump logo to offset 0x5dc00
            # addr + 0x5dc00
            #ia = int(addr, 16)
            #of = int("0x5dc00", 16)
            #newaddr = ia + of
            #ge.ub_write_dump(ub, path + "fb_logo.dump", hex(newaddr))
            #
            # or use video dump created with bdi
            #loadaddr = "0x12000000"
            #ret = ub.exec("ping", "192.168.1.1")
            #while ret[0] != 0:
            #    ret = ub.exec("ping", "192.168.1.1")
            #ub.exec0("tftp", loadaddr, "aristainetos/20190507/fb.dump")
            #ub.exec0("cp", loadaddr, addr, "40000")
            #ub.exec0("lgset")
            """
            if interactive:
                ub.interactive()

ub_resfiles = [
    "System.map",
    "u-boot-dtb.bin",
    "u-boot-dtb.imx",
]

@tbot.testcase
def aristainetos_ub_build(
    lab: typing.Optional[linux.LinuxShell] = None,
) -> None:
    """
    build u-boot
    """
    ge.ub_build("aristainetos2", ub_resfiles)

    # create "u-boot-dtb.imx.signed"
    f = "u-boot-dtb.imx"
    tbot.log.message(tbot.log.c(f"Creating signed {f}").green)
    # copy u-boot-dtb.imx to sign directory
    with lab or tbot.acquire_lab() as lh:
        r = lh.tftp_root_path / ge.get_path(lh.tftp_dir_board)
        s = r / f
        t = lh.sign_dir
        tbot.tc.shell.copy(s, t)
        lh.exec0("cd", t)
        lh.exec0("./cst", "--o", "u-boot-dtb_csf.bin", "--i", "u-boot-dtb.csf")
        lh.exec0(linux.Raw(f"cat {f} u-boot-dtb_csf.bin > {f}.signed"))
        lh.exec0("ls", "-al")
        s = lh.sign_dir / f"{f}.signed"
        t = lh.tftp_root_path / ge.get_path(lh.tftp_dir_board)
        tbot.tc.shell.copy(s, t)

@tbot.testcase
def aristainetos_ub_check_version(
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
def aristainetos_ub_build_install_test(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
        aristainetos_ub_build()
        ari_ub_update_i(interactive = False)
        aristainetos_ub_check_version()
        uboot_testpy()

@tbot.testcase
def ari_ub_dump_register(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
    """
    dump U-Boot register into file
    """
    with lab or tbot.acquire_lab() as lh:
        with contextlib.ExitStack() as cx:
            if board is not None:
                b = board
            else:
                b = cx.enter_context(tbot.acquire_board(lh))

            if ubx is not None:
                ub = ubx
            else:
                ub = cx.enter_context(tbot.acquire_uboot(b))

            ge.ub_create_revfile(ub, path + "ccm.dump", "0x20c4000", "0x20c408c")
            ge.ub_create_revfile(ub, path + "ccm_an.dump", "0x20c8000", "0x20c8190")

            ge.ub_create_revfile(ub, path + "pinmux.dump", "0x20e0000", "0x20e093c")
            ge.ub_create_revfile(ub, path + "usdhc1.dump", "0x2190000", "0x21900cc")
            ge.ub_create_revfile(ub, path + "usdhc2.dump", "0x2194000", "0x21940cc")

            ge.ub_create_revfile(ub, path + "gpio1.dump", "0x209c000", "0x209c020")
            ge.ub_create_revfile(ub, path + "gpio2.dump", "0x20a0000", "0x20a0020")
            ge.ub_create_revfile(ub, path + "gpio3.dump", "0x20a4000", "0x20a4020")
            ge.ub_create_revfile(ub, path + "gpio4.dump", "0x20a8000", "0x20a8020")
            ge.ub_create_revfile(ub, path + "gpio5.dump", "0x20ac000", "0x20ac020")
            ge.ub_create_revfile(ub, path + "gpio6.dump", "0x20b0000", "0x20b0020")
            ge.ub_create_revfile(ub, path + "gpio7.dump", "0x20b4000", "0x20b4020")

            ge.ub_create_revfile(ub, path + "pwm1.dump", "0x2080000", "0x2080018")
            ge.ub_create_revfile(ub, path + "pwm2.dump", "0x2084000", "0x2084018")
            ge.ub_create_revfile(ub, path + "pwm3.dump", "0x2088000", "0x2088018")
            ge.ub_create_revfile(ub, path + "pwm4.dump", "0x208c000", "0x208c018")

            ge.ub_create_revfile(ub, path + "ecspi1.dump", "0x2008000", "0x2008044")
            ge.ub_create_revfile(ub, path + "ecspi2.dump", "0x200c000", "0x200c044")
            ge.ub_create_revfile(ub, path + "ecspi3.dump", "0x2010000", "0x2010044")
            ge.ub_create_revfile(ub, path + "ecspi4.dump", "0x2014000", "0x2014044")

            ge.ub_create_revfile(ub, path + "enet1.dump", "0x2188000", "0x21881c4")

            ge.ub_create_revfile(ub, path + "ipu1.dump", "0x2600000", "0x260028c")
            ge.ub_create_revfile(ub, path + "ipu1_dmac.dump", "0x2608000", "0x2608108")
            ge.ub_create_revfile(ub, path + "ipu1_dp.dump", "0x2618000", "0x2618118")
            ge.ub_create_revfile(ub, path + "ipu1_ic.dump", "0x2620000", "0x262028")
            ge.ub_create_revfile(ub, path + "ipu1_csi0.dump", "0x2630000", "0x26300f0")
            ge.ub_create_revfile(ub, path + "ipu1_csi1.dump", "0x2638000", "0x26380f0")
            ge.ub_create_revfile(ub, path + "ipu1_diu0.dump", "0x2640000", "0x2640178")
            ge.ub_create_revfile(ub, path + "ipu1_diu1.dump", "0x2648000", "0x2648178")
            ge.ub_create_revfile(ub, path + "ipu1_dc.dump", "0x2658000", "0x26581cc")
            # ge.ub_create_revfile(ub, path + "fb_logo.dump", "0x4bf96cc0", "0x4bfa1ff0")

@tbot.testcase
def ari_ub_check_register(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
    """
    check U-Boot register
    """
    with lab or tbot.acquire_lab() as lh:
        with contextlib.ExitStack() as cx:
            if board is not None:
                b = board
            else:
                b = cx.enter_context(tbot.acquire_board(lh))

            if ubx is not None:
                ub = ubx
            else:
                ub = cx.enter_context(tbot.acquire_uboot(b))

            if "lg4573" in ub.bootlog:
                ub.exec0("lgset")
            path = "tc/aristainetos/files/"
            files = [
                "ccm.dump",
                "ccm_an.dump",
                "pinmux.dump",
                "usdhc1.dump",
                "usdhc2.dump",
                "gpio1.dump",
                "gpio2.dump",
                "gpio3.dump",
                "gpio4.dump",
                "gpio5.dump",
                "gpio6.dump",
                "gpio7.dump",
                "pwm1.dump",
                "pwm2.dump",
                "pwm3.dump",
                "pwm4.dump",
                "ecspi1.dump",
                "ecspi2.dump",
                "ecspi3.dump",
                "ecspi4.dump",
                "enet1.dump",
                "ipu1.dump",
                "ipu1_dmac.dump",
                "ipu1_dp.dump",
                "ipu1_ic.dump",
                "ipu1_csi0.dump",
                "ipu1_csi1.dump",
                "ipu1_diu0.dump",
                "ipu1_diu1.dump",
                "ipu1_dc.dump",
                "ldb.dump",
                ]
            files = ["pinmux.dump"]
            files = ["ipu1.dump", "ipu1_dmac.dump", "ipu1_dp.dump", "ipu1_ic.dump",
                     "ipu1_csi0.dump", "ipu1_csi1.dump", "ipu1_diu0.dump",
                     "ipu1_diu1.dump", "ipu1_dc.dump", "ldb.dump",
                    ]
            files = [
                "gpio1.dump",
                "gpio2.dump",
                "gpio3.dump",
                "gpio4.dump",
                "gpio5.dump",
                "gpio6.dump",
                "gpio7.dump",
                    ]
            files = [
                "ccm.dump",
                "ccm_an.dump",
                    ]
            files = ["ipu1.dump", "ipu1_dmac.dump", "ipu1_dp.dump", "ipu1_ic.dump",
                     "ipu1_csi0.dump", "ipu1_csi1.dump", "ipu1_diu0.dump",
                     "ipu1_diu1.dump", "ipu1_dc.dump", "ldb.dump",
                    "ccm.dump",
                    "ccm_an.dump",
                    ]
            files = ["pinmux.dump"]
            for f in files:
                #ge.ub_check_revfile(ub, path + f, "diff_pinmux.txt", "/home/hs/data/Entwicklung/prozessordoku/imx6/IMX6SDLRM.txt")
                ge.ub_check_revfile(ub, path + f)

@tbot.testcase
def ari_ub_check_i2c(
    lab: typing.Optional[linux.LinuxShell] = None,
    board: typing.Optional[board.Board] = None,
    ubx: typing.Optional[board.UBootShell] = None,
) -> None:
    """
    check i2c probe and dumps
    """
    with lab or tbot.acquire_lab() as lh:
        with contextlib.ExitStack() as cx:
            if board is not None:
                b = board
            else:
                b = cx.enter_context(tbot.acquire_board(lh))

            if ubx is not None:
                ub = ubx
            else:
                ub = cx.enter_context(tbot.acquire_uboot(b))

            ub.exec0("i2c", "dev", "0")
            log = ub.exec0("i2c", "probe")
            if "58 59 71" not in log:
                raise RuntimeError("Probing bus 0 failed res: {log}")

            ub.exec0("i2c", "dev", "1")
            log = ub.exec("i2c", "probe")
            if log[0] == 0:
                raise RuntimeError("Probing bus 1 failed res: {log}")

            ub.exec0("i2c", "dev", "2")
            log = ub.exec0("i2c", "probe")
            dump_file = i2c_dump_0_58_7
            if "20 4D 68" not in log:
                if "20 4B 68" not in log:
                    raise RuntimeError("Probing bus 2 failed res: {log}")
                else:
                    dump_file = i2c_dump_0_58_4

            ge.ub_check_i2c_dump(ub, "0", "0x58", dump_file)
