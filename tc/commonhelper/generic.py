import contextlib
import typing
import tbot
import time
from tbot.machine import board, channel, linux, connector
from tbot import log_event
from tbot import log
import math
import os
import re
from datetime import datetime
from tbot.tc.uboot import build as uboot_build
from tbot import log_event
from tbot.tc.uboot import testpy as uboot_testpy

def search_string_in_multiline(search, lines) -> bool:
    """
    search string search in multiline lines
    """
    for l in lines.split('\n'):
        if search in l:
            return True

    return False

def get_pid(ma: linux.LinuxShell) -> str:
    """
    get PID of last command
    """
    ma.ch.sendline("echo $!", read_back=True)
    pid = ma.ch.read_until_prompt()
    pid = pid.strip()
    return pid

def get_path(path : tbot.machine.linux.Path) -> str:
    """
    return the path from a pathlib
    """
    return path._local_str()

def get_ub_tftp_path(ma: linux.LinuxShell, path : tbot.machine.linux.Path) -> str:
    """
    return the tftp path for u-boot tftp command
    """
    pt = path._local_str()
    return os.path.relpath(pt, ma.tftproot)

@tbot.testcase
def get_board_workdir(
    ma: linux.LinuxShell,
) -> str:
    p2 = ma.workdir / tbot.selectable.Board.name
    if not p2.exists():
        ma.exec0("mkdir", "-p", p2)
    return p2

@tbot.testcase
def get_toolchain_dir(
    ma: linux.LinuxShell,
) -> str:
    """
    return path where toolchains are installed.

    :param LinuxMachine: Linux machine
    """
    p2 = ma.workdir / "toolchain"
    if not p2.exists():
        ma.exec0("mkdir", "-p", p2)
    return p2

@tbot.testcase
def set_toolchain(
    ma: linux.LinuxShell,
    arch = "armv7-eabihf",
    libc = "glibc",
    typ = "stable",
    date = "2018.11-1",
) -> None:
    """
    download and set a toolchain from:

    https://toolchains.bootlin.com/downloads/releases/toolchains/

    !! Bootlin toolchain does not work for U-Boot as there are
       problems with relocate-sdk.sh script !!

    Also, this part is integrated into tbot now:
    tbot/machine/linux/build/toolchain.py
    search for EnvSetBootlinToolchain

    :param LinuxMachine: Linux machine:
    :param str arch: architecture, default "armv7-eabihf"
    :param str libc: used libc. default "glibc"
    :param str typ: "stable" or "bleeding-edge", defaule "stable"
    :param str date: "2018.11-1"
    """
    log_event.doc_tag("set_bootlin_toolchain_arch_fixlen", arch)
    log_event.doc_tag("set_bootlin_toolchain_libc_fixlen", libc)
    log_event.doc_tag("set_bootlin_toolchain_typ_fixlen", typ)
    log_event.doc_tag("set_bootlin_toolchain_date_fixlen", date)
    log_event.doc_begin("set_toolchain_check_installed")
    td = get_toolchain_dir(ma)
    ma.exec0("cd", td)
    fn = arch + "--" + libc + "--" + typ + "-" + date
    fn2 = arch + "/tarballs/" + fn
    ending = ".tar.bz2"
    tooldir = td / fn / "bin"
    ret = ma.exec("test", "-d", tooldir)
    log_event.doc_end("set_toolchain_check_installed")
    if ret[0] == 1:
        log_event.doc_begin("set_toolchain_install")
        msg = "Get toolchain " + fn
        tbot.log.message(msg)
        ma.exec0("wget", "https://toolchains.bootlin.com/downloads/releases/toolchains/" + fn2 + ending)
        ma.exec0("tar", "xfj", fn + ending)
        ma.exec0("cd", fn)
        ma.exec0("./relocate-sdk.sh")
        log_event.doc_end("set_toolchain_install")
    ret = ma.exec("printenv", "PATH", tbot.machine.linux.Pipe, "grep", "--color=never", tooldir)
    if ret[0] == 1:
        log_event.doc_begin("set_toolchain_add")
        tbot.log.message(f"Add toolchain to PATH ({tooldir})")
        old_path = ma.env("PATH")
        ma.env("PATH", linux.F("{}:{}", tooldir, old_path))
        log_event.doc_end("set_toolchain_add")
    ma.exec0("printenv", "PATH")
    if "arm" in arch:
        log_event.doc_begin("set_toolchain_set_shell_vars")
        ma.exec0("export", "ARCH=arm" )
        ma.exec0("CROSS_COMPILE=arm-linux-")
        log_event.doc_end("set_toolchain_set_shell_vars")

@tbot.testcase
def cd_board_workdir(
    ma: linux.LinuxShell,
) -> None:
    p = get_board_workdir(ma)
    bh.exec0("cd", p)

# misc

def string_to_dict(string, pattern):
    """ convert a string into a dictionary via a pattern
        example pattern:
        'hello, my name is {name} and I am a {age} year old {what}'
        string:
        'hello, my name is dan and I am a 33 year old developer'
        returned dict:
        {'age': '33', 'name': 'dan', 'what': 'developer'}
        from:
        https://stackoverflow.com/questions/11844986/convert-or-unformat-a-string-to-variables-like-format-but-in-reverse-in-p
    """
    regex = re.sub(r'{(.+?)}', r'(?P<_\1>.+)', pattern)
    values = list(re.search(regex, string).groups())
    keys = re.findall(r'{(.+?)}', pattern)
    _dict = dict(zip(keys, values))
    return _dict

def recv_prompt(
    ma: linux.LinuxShell,
    cmd: str,
    prompt,
    count,
    timeout: typing.Optional[float] = None,
    ) -> dict:
    """
    receive until prompt is count times received
    than send break to finish command.
    returns a dictionary with the received parts.
    """
    res = []
    withcmd = True
    if cmd == None:
        withcmd = False
        cmd = ""
    with tbot.log_event.command(ma.name, cmd) as ev, ma.ch.with_stream(ev, False):
        if withcmd:
            ma.ch.sendline(cmd)
        buf = b""
        for frag in ma.ch.read_iter(timeout=timeout):
            buf += frag
            if buf.count(prompt) >= count:
                break
        if withcmd:
            ma.ch.sendintr()
            buf += ma.ch.read_until_prompt(timeout=timeout).encode()

    buf = buf.decode(errors="replace")
    for l in buf.split(prompt.decode(errors="replace")):
        res.append({"out": l.strip()})

    return res

def recv_count_lines(
    ma: linux.LinuxShell,
    prompt,
    count: int,
    *args: typing.Union[str]
) -> dict:
    """
    send a command and receive count lines with prompt
    than send a break and return the received "lines"
    in a dictionary.
    """
    command = ma.escape(*args)
    return recv_prompt(ma, command, prompt, count)

def recv_timeout(
    ch,
    name,
    endstr,
    tout
) -> typing.Tuple[int, bytes]:
    """
    receive on channel ch until tout

    ToDo: pass a string, which marks end. If string found return 0

    :param ch: channel
    :param str name: String used for logging
    :param bbytess endstr: if != "" and string found end with retval = 0
    :param fload tout: timeout
    :returns: bytes
    """
    raw = b""
    end = b""
    retval = 1
    with log_event.command("pickup", name) as ev:
        loop = True
        while loop:
            try:
                raw += ch.recv_n(1, timeout=tout)
            except TimeoutError:
                loop = False
                pass
            try:
                ev.write(raw.decode("utf-8"))
                end += raw
                raw = b""
            except UnicodeDecodeError:
                ev.write(raw.decode("latin1"))
                end += raw
                raw = b""

            if endstr != b"":
                if endstr in end:
                    retval = 0
                    loop = False

    return retval, end

# linux testcases
@tbot.testcase
def lx_replace_in_file(
    ma: linux.LinuxShell,
    filename,
    searchstring,
    newvalue,
    use_sudo = False,
    dumpfile = True,
) -> bool:
    """
    replace searchstring in filename which with newvalue

    :param machine ma: machine on which commands are executed
    :param filename str: filename of file on which testcase runs
    :param searchstring str: line which contain this string gets deleted
    :param newvalue str: newline which get added to the end of file
    :param use_sudo bool: use sudo default False
    :param dumpfile bool: dump file with cat before and after replace string default True
    """
    pre = []
    if use_sudo:
        pre = ["sudo"]

    if dumpfile:
        ma.exec0(*pre, "cat", filename)

    ma.exec0(*pre, "sed", "-i", f"/{searchstring}/{newvalue}/d", filename)

    if dumpfile:
        ma.exec0(*pre, "cat", filename)

    return True

@tbot.testcase
def lx_replace_line_in_file(
    ma: linux.LinuxShell,
    filename,
    searchstring,
    newvalue,
    use_sudo = False,
    dumpfile = True,
) -> bool:
    """
    replace a line in filename which contains searchstring
    with line containing newvalue

    :param machine ma: machine on which commands are executed
    :param filename str: filename of file on which testcase runs
    :param searchstring str: line which contain this string gets deleted
    :param newvalue str: newline which get added to the end of file
    :param use_sudo bool: use sudo default False
    :param dumpfile bool: dump file with cat before and after replace string default True
    """
    pre = []
    if use_sudo:
        pre = ["sudo"]

    if dumpfile:
        ma.exec0(*pre, "cat", filename)

    ma.exec0(*pre, "sed", "-i", f"/{searchstring}/d", filename)
    ma.exec0(*pre, "echo", newvalue, linux.Raw(">>"), filename)

    if dumpfile:
        ma.exec0(*pre, "cat", filename)

    return True


@tbot.testcase
def lx_cmd_exists(
    ma: linux.LinuxShell,
    cmd,
) -> bool:
    ret = ma.exec(linux.Raw(("command -v " + cmd + " >/dev/null 2>&1")))
    if ret[0] == 0:
        return True
    return False

@tbot.testcase
def lx_devmem2_get(
    ma: linux.LinuxShell,
    addr,
    typ,
) -> str:
    strings = ['Value at address', 'Read at address']
    ret = ma.exec0("devmem2", addr, typ).splitlines()
    for l in ret:
        if any(s in l for s in strings):
            val = l.split(" ")
            return val[-1]

    raise RuntimeError("devmem2 unexpected output")

@tbot.testcase
def lx_get_uboot_var(
    ma: linux.LinuxShell,
    varname,
) -> str:
    ret = ma.exec0("fw_printenv", varname)
    return ret

@tbot.testcase
def lx_check_revfile(
    ma: linux.LinuxShell,
    revfile,
    difffile = None,
    timeout = None,
) -> bool:
    # check if devmem exist
    ret = lx_cmd_exists(ma, 'devmem2')
    if ret == False:
        return

    ret = True
    try:
        fd = open(revfile, 'r')
    except IOError:
        raise RuntimeError("Could not open: " + revfile)

    if difffile != None:
        try:
            fddiff = open(difffile, 'a')
        except IOError:
            raise RuntimeError("Could not open diffile: " + difffile)

    lnr = 0
    for line in fd.readlines():
        lnr += 1
        cols = line.split()
        if cols[0] == '#':
            continue

        val = lx_devmem2_get(ma, cols[0], cols[2])
        msg = f"diff args: {revfile} line: {lnr} {val}@{cols[0]} & {cols[1]} != {cols[3]}"
        if (int(val, 16) & int(cols[1], 16)) != (int(cols[3], 16) & int(cols[1], 16)):
            tbot.log.message(tbot.log.c(msg).red)
            if difffile != None:
                fddiff.write(msg + "\n")

            ret = False

        if timeout != None:
            time.sleep(timeout)

    fd.close()
    if difffile != None:
        fddiff.close()
    return ret

@tbot.testcase
def lx_create_revfile(
    ma: linux.LinuxShell,
    revfile,
    startaddr,
    endaddr,
    mask = '0xffffffff',
    readtype = 'w',
) -> bool:
    # check if devmem exist
    ret = lx_cmd_exists(ma, 'devmem2')
    if ret == False:
        return False

    try:
        fd = open(revfile, 'w')
    except IOError:
        raise RuntimeError("Could not open: " + revfile)

    ret = ma.exec0("uname", "-a").splitlines()
    vers = ret[0]

    processor = "ToDo"
    hw = 'ToDo'

    fd.write("# pinmux\n")
    fd.write("# processor: %s\n" % processor)
    fd.write("# hardware : %s\n" % hw)
    fd.write("# Linux    : %s\n" % vers)
    fd.write("# regaddr mask type defval\n")

    start = int(startaddr, 16)
    stop = int(endaddr, 16)

    if readtype == 'w':
        step = 4
    if readtype == 'h':
        step = 2
    if readtype == 'b':
        step = 1

    for i in iter(range(start, stop, step)):
        val = lx_devmem2_get(ma, hex(i), readtype)
        fd.write('%-10s %10s %10s %10s\n' % (hex(i), mask, readtype, val))

    fd.close()
    return True

@tbot.testcase
def lx_check_dmesg(
    ma: linux.LinuxShell,
    dmesg_strings = None,
    dmesg_false_strings = None,
) -> bool:
    """
    check if dmesg output contains strings in dmesg_list

    :param machine ma: machine on which dmesg command is executed
    :param list dmesg_strings: list of strings which must be in dmesg
    :param list dmesg_false_strings: list of strings which sould not occur in dmesg
    """
    buf = ma.exec0("dmesg")
    ret = True
    if dmesg_strings != None:
        for s in dmesg_strings:
            if s not in buf:
                msg = f"String {s} not in dmesg output."
                tbot.log.message(msg)
                ret = False

    if dmesg_false_strings != None:
        for s in dmesg_false_strings:
            if s in buf:
                msg = f"String {s} in dmesg output."
                tbot.log.message(msg)
                ret = False

    return ret

@tbot.testcase
def lx_check_cmd(
    ma: linux.LinuxShell,
    cmd_dict,
) -> bool:
    """
    check commands in list of dictionaries cmd_dict.
    for each element in list execute command cmd_dict["cmd"] and
    if cmd_dict["val"] != "undef" check if cmd_dict["val"]
    is in command output

    :param machine ma: machine on which commands are executed
    :param dict cmd_dict: list of dictionary with command and return values.
    """
    for c in cmd_dict:
        cmdret = ma.exec0(linux.Raw(c["cmd"]))
        if c["val"] != "undef":
            if c["val"] not in cmdret:
                raise RuntimeError(c["val"] + " not found in " + cmdret)

    return True

# should be in machine
path_sys = "/sys"
path_gpio = f"{path_sys}/class/gpio"
@tbot.testcase
def lx_gpio(
    ma: linux.LinuxShell,
    nr: str,
    state: str,
    mode: str = "set",
) -> str:
    """
    if {mode} == "set" (default):
        set gpio {nr} to {state} "on" or "off"
    else if {mode} == "get"
        return state of gpio 0 = "off", 1 = "on"
    returns state
    """
    ret = ma.exec("ls", f"{path_gpio}/gpio{nr}")
    if ret[0] != 0:
        ma.exec0("echo", nr, linux.Raw(">"), f"{path_gpio}/export")
        ma.exec0("ls", f"{path_gpio}/gpio{nr}")

    if mode == "get":
        ma.exec0("echo", "in", linux.Raw(">"), f"{path_gpio}/gpio{nr}/direction")
        ret = ma.exec0("cat", f"{path_gpio}/gpio{nr}/value")
        if ret.strip() == "0":
            return "off"
        elif ret.strip() == "1":
            return "on"
        else:
            raise RuntimeError(f"unknown gpio state {ret}")
    elif mode == "set":
        if state == "on":
            val = "1"
        else:
            val = "0"

        ma.exec0("echo", "out", linux.Raw(">"), f"{path_gpio}/gpio{nr}/direction")
        ma.exec0("echo", val, linux.Raw(">"), f"{path_gpio}/gpio{nr}/value")
    else:
        raise RuntimeError(f"unknown mode {mode}")

    return state


# U-Boot
@tbot.testcase
def ub_build(
    name: str,
    resfiles: list,
    lab: typing.Optional[linux.LinuxShell] = None,
    build: typing.Optional[linux.LinuxShell] = None,
) -> None:
    """
    build u-boot and generate doc tags
    """
    with lab or tbot.acquire_lab() as lh:
        git = uboot_build(lab=lh)

        log_event.doc_tag("UBOOT_BOARD_NAME", name)
        today = datetime.now()
        log_event.doc_tag("UBOOT_BUILD_TIME", today.strftime("%Y-%m-%d %H:%M:%S"))
        log_event.doc_tag("UBOOT_BUILD_TITLE", f"tbot automated build of {name}")
        log_event.doc_tag("UBOOT_NOTES", "built with tbot")
        hasspl = False
        for f in resfiles:
            s = git / f
            r = lh.tftp_root_path / get_path(lh.tftp_dir_board)
            t = r / f
            p = get_path(t)
            tbot.tc.shell.copy(s, t)
            lh.exec0("chmod", "666", t)
            if f == "MLO" or f == "SPL":
                ret = lh.exec0("ls", "-al", p, linux.Pipe, "cut", "-d", " ", "-f", "5")
                log_event.doc_tag("UBOOT_SPL_SIZE", ret.strip())
                hasspl = True
            if f == "u-boot.img" or f == "u-boot-socrates.bin":
                ret = lh.exec0("ls", "-al", p, linux.Pipe, "cut", "-d", " ", "-f", "5")
                log_event.doc_tag("UBOOT_UBOOT_SIZE", ret.strip())
        if not hasspl:
            log_event.doc_tag("UBOOT_SPL_SIZE", "0")

@tbot.testcase
@tbot.with_uboot
def ub_check_i2c_dump(ub, dev, address, i2c_dump) -> bool:
    """
    dev      : i2c dev number
    address  : i2c addr
    i2c_dump : list
    sample_i2c_dump = [
        "0x00: 11 00 00 21 00 01 3f 01 00 7f 00 00 00 00 00 81",
        "0x10: 00 00 3f 00 00 00 00 00 00 00 00 10 ad de xx xx",
    ]
    before ":" start address, after list of values
               'xx' ignore
    """
    retval = True
    ub.exec0("i2c", "dev", dev)
    for l in i2c_dump:
        addr, values, *_ = l.split(":")
        values = values.split(" ")
        ad = int(addr, 0)
        for v in values:
            if v == '':
                continue
            if v == 'xx':
                ad += 1
                continue
            adh = format(ad, '02x')
            ret = ub.exec0("i2c", "md", address, adh + ".1", "1")
            rval = ret.split(":")[1]
            rval = rval.split(" ")[1]
            if rval != str(v):
                tbot.log.message(tbot.log.c(f"diff for device {address} on bus {dev} found @{adh} {rval} != {v}").red)
                retval = False
            ad += 1

    return retval

@tbot.testcase
def ub_get_var(
    ub: board.UBootShell,
    name,
) -> str:
    ret = ub.exec0("printenv", name)
    return ret.split("=")[1].strip()

def ub_check_size(
    size,
) -> bool:
    if any(i in size for i in ('b', 'w', 'l')):
        return True
    else:
        raise RuntimeError(f"size {size} not supported.")

@tbot.testcase
def ub_get_mem_addr(
    ub: board.UBootShell,
    addr,
    size,
) -> str:
    """
    address  : memory addr
    size: b, w or l
    """
    ub_check_size(size)

    ret = ub.exec(f"md.{size}", addr, "1")
    if ret[0] != 0:
        raise RuntimeError(f"Error reading {addr} {ret}")
    return "0x" + ret[1].split(" ")[1]

@tbot.testcase
def ub_set_mem_addr(
    ub: board.UBootShell,
    addr,
    size,
    value,
    count = "1",
) -> None:
    """
    address  : memory addr
    size : b, w or l
    value: the value
    count : count
    """
    ub_check_size(size)

    ret = ub.exec(f"mw.{size}", addr, value, count)
    if ret[0] != 0:
        raise RuntimeError(f"Error wrinting {addr} {value} {ret}")

@tbot.testcase
def ub_create_revfile(
    ub: board.UBootShell,
    revfile,
    startaddr,
    endaddr,
    mask = '0xffffffff',
    size = 'l',
) -> bool:
    ub_check_size(size)

    try:
        fd = open(revfile, 'w')
    except IOError:
        raise RuntimeError("Could not open: " + revfile)

    vers = ub.exec0("vers")

    fd.write("# U-Boot   :\n")
    vers = vers.split("\n")
    for line in vers:
        fd.write("# %s\n" % line)
    fd.write("# regaddr mask type defval\n")

    start = int(startaddr, 16)
    stop = int(endaddr, 16)

    if size == 'l':
        step = 4
    if size == 'w':
        step = 2
    if size == 'b':
        step = 1

    for i in iter(range(start, stop, step)):
        val = ub_get_mem_addr(ub, hex(i), size)
        fd.write('%-10s %10s %10s %10s\n' % (hex(i), mask, size, val))

    fd.close()
    return True

def get_name(socfile, addr):
    """
    you need the RM converted from pdf to txt, used
    https://www.pdf2go.com/de/pdf-in-text
    for converting ...
    """
    if socfile == None:
        return

    try:
        fd = open(socfile, 'r')
    except IOError:
        raise RuntimeError("Could not open: " + socfile)

    oldline = ""
    lines = fd.readlines()
    addr = addr.replace("0x", "")
    addr = addr.upper()
    last = addr[-4:]
    rest = addr[:-4]
    addr = rest + "_" + last + "h"
    for line in lines:
        if addr in line:
            oldline = oldline.replace("(", "")
            oldline = oldline.replace(")", "")
            fd.close()
            return oldline

        oldline = line

    fd.close()
    return "notfound\n"

@tbot.testcase
def ub_write_dump(
    ub: board.UBootShell,
    revfile,
    newaddr,
) -> bool:
    """
    write content of revfile into memory.
    """
    ret = True
    try:
        fd = open(revfile, 'r')
    except IOError:
        raise RuntimeError("Could not open: " + revfile)

    off = None

    tbot.log.message(f"dump {revfile} to {newaddr}")
    lnr = 0
    for line in fd.readlines():
        lnr += 1
        cols = line.split()
        if cols[0] == '#':
            continue

        if off == None:
            if newaddr == cols[0]:
                off = 0
            else:
                inew = int(newaddr, 16)
                icol = int(cols[0], 16)
                off = inew - icol

        icol = int(cols[0], 16)
        addr = icol + off
        ub_set_mem_addr(ub, hex(addr), cols[2], cols[3])

@tbot.testcase
def ub_check_revfile(
    ub: board.UBootShell,
    revfile,
    difffile = None,
    socfile = None,
) -> bool:
    ret = True
    try:
        fd = open(revfile, 'r')
    except IOError:
        raise RuntimeError("Could not open: " + revfile)

    if difffile != None:
        try:
            fddiff = open(difffile, 'a')
        except IOError:
            raise RuntimeError("Could not open: " + difffile)

    tbot.log.message(f"Checking file {revfile}")
    lnr = 0
    for line in fd.readlines():
        lnr += 1
        cols = line.split()
        if cols[0] == '#':
            continue

        val = ub_get_mem_addr(ub, cols[0], cols[2])
        if (int(val, 16) & int(cols[1], 16)) != (int(cols[3], 16) & int(cols[1], 16)):
            msg = f"diff args: {revfile} line: {lnr} {val}@{cols[0]} & {cols[1]} != {cols[3]}"
            tbot.log.message(tbot.log.c(msg).red)
            if difffile != None:
                fddiff.write(msg + "\n")
                fddiff.write(get_name(socfile, cols[0]))

            ret = False

    fd.close()
    if difffile != None:
        fddiff.close()

    return ret

@tbot.testcase
def lx_check_iperf(
    lh: linux.LinuxShell,
    lnx: linux.LinuxShell,
    intervall = "1",
    cycles = "10",
    minval = "80",
    filename = "iperf.dat",
    showlog = False,
) -> bool:
    """
    check networkperformance with iperf
    intervall: "-i" iperf paramter in seconds
    cycles: "-t" iperf parameter
    minval: if bandwith is lower than this value, fail
    """
    result = []
    ymax = "0"
    unit = "MBits/sec"
    error = False
    # check on labhost, if iperf server runs
    # if not start it
    ret = lh.exec0("ps", "afx", linux.Pipe , "grep", "iperf")
    start = True
    for l in ret.split("\n"):
        if "iperf" in l and not "grep" in l:
            start = False
    if start:
        #ret = lh.exec("iperf", "-s", linux.Background)
        lh.ch.sendline("iperf -s &")
        time.sleep(1)
    oldverbosity = log.VERBOSITY
    if showlog:
        log.VERBOSITY = log.Verbosity.STDOUT
    xmax = str(int(cycles) * int(intervall))
    log_event.doc_tag("iperf_unit", unit)
    log_event.doc_tag("iperf_minval", minval)
    log_event.doc_tag("iperf_cycles", cycles)
    log_event.doc_tag("iperf_intervall", intervall)
    log_event.doc_begin("iperf_test")
    ret = lnx.exec0("iperf", "-c", lh.serverip, "-i", intervall, "-t", xmax)
    lowestval = "1000000"
    step = str(float(intervall) / 2)
    for l in ret.split("\n"):
        if "Mbits/sec" in l or "Kbits/sec" in l or "bits/sec" in l:
            tmp = l.split(" ")
            val = tmp[-2]
            if "Kbits/sec" in l:
                val = str(float(val) / 1000)
            if "bits/sec" in l and not ("Mbits/sec" in l or "Kbits/sec" in l):
                val = str(float(val) / 1000)
            result.append({"bandwith" : val, "step" : step})
            if float(ymax) < float(val):
                ymax = val
            if float(val) < float(minval):
                if error == False:
                    tbot.log.message(tbot.log.c(f"Not enough Bandwith {val} < {minval}").red)
                error = True
            if float(lowestval) > float(val):
                lowestval = val
            step = str(float(step) + float(intervall))

    if error:
        log_event.doc_tag("iperf_result", f"not enough Bandwith {lowestval} {unit} < {minval} {unit}")
    else:
        log_event.doc_tag("iperf_result", f"enough Bandwith {lowestval} {unit} >= {minval} {unit}")

    log_event.doc_end("iperf_test")
    log.VERBOSITY = oldverbosity
    # remove last line, as it is not a measurement
    result = result[:-1]
    step = 0
    # round up ymax
    ymax = str(int(math.ceil(float(ymax) / 10.0)) * 10)
    fd = open('results/iperf/' + filename, 'w')
    # save the xmax and ymax value behind the headlines
    # gnuplot uses them for setting the correct xmax / ymax values
    fd.write(f"step bandwith minimum {xmax} {ymax}\n")
    for el in result:
        s = str(step)
        fd.write(f'{el["step"]} {el["bandwith"]} {minval}\n')
        step += int(intervall)
    fd.close()

    if error:
        raise RuntimeError(f"Not enough Bandwith {lowestval} < {minval}")
    else:
        tbot.log.message(tbot.log.c(f"Bandwith always above minimum {minval} MBit/s").green)
    return True

@tbot.testcase
def lx_check_latency(
    ma: linux.LinuxShell,
    count: str = "50",
    latency_max: str = "20",
    filename: str = "latency.dat",
) -> bool:
    """
    call latency command and print results into latency.dat
    count: how many lines with "RTD" will be read
    latency_max: max value of allowed latency
    filename: for datfile
    """
    # RTT|  00:00:01  (periodic user-mode task, 1000 us period, priority 99)
    # RTH|----lat min|----lat avg|----lat max|-overrun|---msw|---lat best|--lat worst
    # RTD|     11.458|     16.702|     39.250|       0|     0|     11.458|     39.250
    rtd_format = 'RTD\|{min}\|{avg}\|{max}\|{overrun}\|{msw}\|{best}\|{worst}'
    rtd = []
    result = True
    ret = recv_count_lines(ma, b"\n", count, "latency", "-g", "results/latency/latency.dat")
    #
    # killing does not work, as after the prompt there comes more
    # output from the latency test, which confuses tbot
    # ret = lnx.exec0(linux.Raw("latency -g results/latency/latency.dat & sleep 15 ; kill %%"))
    ymax = 0
    for l in ret:
        if 'RTD' in l["out"]:
            rtd_dict = string_to_dict(l["out"], rtd_format)
            rtd.append(rtd_dict)
            if float(latency_max) < float(rtd_dict['max']):
                tbot.log.message(tbot.log.c(f"measured latency {rtd_dict['max']} greater than allowed maximal latency {latency_max}").red)
                result = False
            if float(rtd_dict['overrun']) != 0:
                tbot.log.message(tbot.log.c(f"overrun {rtd_dict['overrun']}").red)
                result = False
            if float(rtd_dict['max']) > ymax:
                ymax = float(rtd_dict['max'])

    # round up ymax
    if ymax > float(latency_max):
        ymax = str(int(math.ceil(float(ymax) / 10.0)) * 10)
    else:
        ymax = str(int(latency_max) + 5)

    xmax = str(len(rtd))
    fd = open('results/latency/' + filename, 'w')
    # save the xmax, ymax and latency_max value behind the headlines
    # gnuplot uses them for setting the correct xmax / ymax values
    fd.write(f'step lat_min lat_avg lat_max overrun msw lat_best lat_worst {xmax} {ymax} {latency_max}\n')
    step = "0"
    for d in rtd:
        fd.write(f"{step} {d['min']} {d['avg']} {d['max']} {d['overrun']} {d['msw']} {d['best']} {d['worst']}\n")
        step = str(int(step) + 1)

    fd.close()
    return result
