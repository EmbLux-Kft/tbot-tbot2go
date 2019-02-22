import contextlib
import typing
import tbot
from tbot.machine import linux
from tbot.machine import board
from tbot import log_event

def get_path(path : tbot.machine.linux.path.Path) -> str:
    """
    return the path from a pathlib
    """
    return path._local_str()

@tbot.testcase
def get_board_workdir(
    ma: typing.Optional[linux.LinuxMachine],
) -> str:
    p2 = ma.workdir / tbot.selectable.Board.name
    if not p2.exists():
        ma.exec0("mkdir", "-p", p2)
    return p2

@tbot.testcase
def get_toolchain_dir(
    ma: typing.Optional[linux.LinuxMachine],
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
    ma: typing.Optional[linux.LabHost],
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
        msg = "Add toolchain to PATH", get_path(tooldir)
        tbot.log.message(msg)
        ma.exec0(linux.Raw("export PATH=" + get_path(tooldir) + ":$PATH"))
        log_event.doc_end("set_toolchain_add")
    ma.exec0("printenv", "PATH")
    if "arm" in arch:
        log_event.doc_begin("set_toolchain_set_shell_vars")
        ma.exec0("export", "ARCH=arm" )
        ma.exec0("CROSS_COMPILE=arm-linux-")
        log_event.doc_end("set_toolchain_set_shell_vars")

@tbot.testcase
def cd_board_workdir(
    ma: typing.Optional[linux.LinuxMachine],
) -> None:
    p = get_board_workdir(ma)
    bh.exec0("cd", p)

# misc
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
    ma: typing.Optional[linux.LinuxMachine],
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
    pre = ""
    if use_sudo:
        pre = "sudo "

    dump = pre + "cat " + filename
    if dumpfile:
        ma.exec0(linux.Raw(dump))

    cmd = pre + "sed -i '/" + searchstring + "/" + newvalue + "/d' " + filename
    ma.exec0(linux.Raw(cmd))

    if dumpfile:
        ma.exec0(linux.Raw(dump))

    return True

@tbot.testcase
def lx_replace_line_in_file(
    ma: typing.Optional[linux.LinuxMachine],
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
    pre = ""
    if use_sudo:
        pre = "sudo "

    dump = pre + "cat " + filename
    if dumpfile:
        ma.exec0(linux.Raw(dump))

    cmd = pre + "sed -i '/" + searchstring + "/d' " + filename
    ma.exec0(linux.Raw(cmd))
    cmd = pre + "echo '" + newvalue + "' >> " + filename
    ma.exec0(linux.Raw(cmd))

    if dumpfile:
        ma.exec0(linux.Raw(dump))

    return True


@tbot.testcase
def lx_cmd_exists(
    ma: typing.Optional[linux.LinuxMachine],
    cmd,
) -> bool:
    ret = ma.exec(linux.Raw(("command -v " + cmd + " >/dev/null 2>&1")))
    if ret[0] == 0:
        return True
    return False

@tbot.testcase
def lx_devmem2_get(
    ma: typing.Optional[linux.LinuxMachine],
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
    ma: typing.Optional[linux.LinuxMachine],
    varname,
) -> str:
    ret = ma.exec0("fw_printenv", varname)
    print ("===== varname ", varname, ret)
    return "ToDo"

@tbot.testcase
def lx_check_revfile(
    ma: typing.Optional[linux.LinuxMachine],
    revfile,
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

    lnr = 0
    for line in fd.readlines():
        lnr += 1
        cols = line.split()
        if cols[0] == '#':
            continue

        val = lx_devmem2_get(ma, cols[0], cols[2])
        if (int(val, 16) & int(cols[1], 16)) != (int(cols[3], 16) & int(cols[1], 16)):
            msg = f"diff args: {revfile} line: {lnr} {val}@{cols[0]} & {cols[1]} != {cols[3]}"
            tbot.log.message(msg)
            ret = False

    return ret

@tbot.testcase
def lx_create_revfile(
    ma: typing.Optional[linux.LinuxMachine],
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

    ret = ma.exec0(linux.Raw("uname -a")).splitlines()
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
    ma: typing.Optional[linux.LinuxMachine],
    dmesg_strings,
) -> bool:
    """
    check if dmesg output contains strings in dmesg_list

    :param machine ma: machine on which dmesg command is executed
    :param list dmesg_strings: list of strings
    """
    buf = ma.exec0("dmesg")
    ret = True
    for s in dmesg_strings:
        if s not in buf:
            msg = f"String {s} not in dmesg output."
            tbot.log.message(msg)
            ret = False

    return ret

@tbot.testcase
def lx_check_cmd(
    ma: typing.Optional[linux.LinuxMachine],
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

# U-Boot
@tbot.testcase
def ub_check_i2c_dump(
    lab: typing.Optional[linux.LabHost],
    board: typing.Optional[board.Board],
    uboot: typing.Optional[board.UBootMachine],
    dev,
    address,
    i2c_dump,
) -> bool:
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
    with lab or tbot.acquire_lab() as lh:
        with board or tbot.acquire_board(lh) as b:
            with uboot or tbot.acquire_uboot(b) as ub:
                ub.exec0("i2c", "dev", dev)
                for l in i2c_dump:
                    addr = l.split(":")[0]
                    values = l.split(":")[1]
                    values = values.split(" ")
                    ad = int(addr, 0)
                    for v in values:
                        if v == '' or v == 'xx':
                            continue
                        adh = format(ad, '02x')
                        ret = ub.exec0("i2c", "md", address, adh + ".1", "1")
                        rval = ret.split(":")[1]
                        rval = rval.split(" ")[1]
                        if rval != str(v):
                            msg = f"diff for device {address} on bus {dev} found @{adh} {rval} != {v}"
                            tbot.log.message(msg)
                            retval = False
                        ad += 1

    return retval


