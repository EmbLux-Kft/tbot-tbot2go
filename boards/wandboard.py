import typing
import tbot
from tbot.machine import channel, board, linux
import generic as ge
from tbot.tc import git

if tbot.selectable.LabHost.name == "small-lab":
    # Use lab specific config
    import smalllaptop as lab
elif tbot.selectable.LabHost.name == "lab1":
    # Use lab specific config
    import lab1 as lab
else:
    raise NotImplementedError("Board not available on this labhost!")

class wandboard(lab.Board):
    name = "wandboard"
    connect_wait = 0.0

ub_env = [
    {"name" : "calc_size", "val" : "setexpr fw_sz ${filesize} / 0x200; setexpr fw_sz ${fw_sz} + 1"},
    {"name" : "load_spl", "val" : "tftp ${loadaddr} ${spl_file};run calc_size"},
    {"name" : "load_ub", "val" : "tftp ${loadaddr} ${ub_file};run calc_size"},
    {"name" : "upd_prep", "val" : "mmc dev 0"},
    {"name" : "upd_spl", "val" : "run upd_prep;mmc write ${loadaddr} 2 ${fw_sz}"},
    {"name" : "upd_ub", "val" : "run upd_prep;mmc write ${loadaddr} 8a ${fw_sz}"},
    {"name" : "cmp_spl", "val" : "run load_spl;mmc read ${cmp_addr_r} 2 ${fw_sz};cmp.b ${loadaddr} ${cmp_addr_r} ${filesize}"},
    {"name" : "cmp_ub", "val" : "run load_ub;mmc read ${cmp_addr_r} 8a ${fw_sz};cmp.b ${loadaddr} ${cmp_addr_r} ${filesize}"},
    {"name" : "optargs", "val" : "run addip"},
    {"name" : "hostname", "val" : "wandboard"},
    {"name" : "netdev", "val" : "eth0"},
    {"name" : "addip", "val" : "setenv bootargs ${bootargs} ip=${ipaddr}:${serverip}:${gatewayip}:${netmask}:${hostname}:${netdev}::off panic=1"},
    {"name" : "upd_all", "val" : "run load_spl upd_spl load_ub upd_ub"},
]

class wandboardUBootBuilder(lab.UBootBuilder):
    name = "wandboard-builder"
    defconfig = "wandboard_defconfig"
    toolchain = "linaro-gnueabi"
    remote = "git@gitlab.denx.de:u-boot/u-boot.git"

    testpy_boardenv = r"""# Config for wandboard
# Set sleep time and margin
env__sleep_time = 10
env__sleep_margin = 1
"""

    def do_checkout(self, target: linux.Path, clean: bool, rev: typing.Optional[str]) -> git.GitRepository:
        branch = "master"
        return git.GitRepository(
            target=target, url=self.remote, clean=clean, rev=branch
        )

    def do_patch(self, repo: git.GitRepository) -> None:
        repo.am(linux.Path(repo.host, "/work/hs/tbot-workdir/patches/wandboard"))

class wandboardUBoot(lab.UBootMachine):
    name = "wandboard-uboot"
    prompt = "=> "
    build = wandboardUBootBuilder()

    def do_set_env( 
        self, ub: board.UBootShell
    ) -> bool:
        ub.env("serverip", tbot.selectable.LabHost.serverip["wandboard"])
        ub.env("netmask", "255.255.255.0")
        ub.env("ipaddr", tbot.selectable.LabHost.boardip["wandboard"])
        ta = ub.host.tftp_dir_board
        f = ta / "SPL"
        ub.env("spl_file", ge.get_path(f))
        f = ta / "u-boot.img"
        ub.env("ub_file", ge.get_path(f))
        ub.env("cmp_addr_r", "11000000")
        for env in ub_env:
            ub.env(env["name"], env["val"])

class wandboardLinuxWithUBoot(board.LinuxUbootConnector, board.LinuxBootLogin, linux.Bash):
    name = "wandboard-lnx"
    uboot = wandboardUBoot
    if tbot.selectable.LabHost.name == "small-lab":
        username = "root"
        password = None
    else:
        username = "debian"
        password = "temppwd"

    def wandboard_lnx_setup(self) -> None:
        ret = self.exec("ifconfig")
        ip = tbot.selectable.LabHost.boardip["wandboard"]
        if str(ip) in ret[1]:
            return
        self.exec0("ifconfig", "eth0", "down", ip, "up")

    # do stuff after linux login
    def init(self):
        self.wandboard_lnx_setup()

    def do_boot(self, ub: board.UBootShell) -> channel.Channel:
        self.uboot.do_set_env(self, ub)
        return ub.boot("run", "bootcmd")

BOARD = wandboard
UBOOT = wandboardUBoot
LINUX = wandboardLinuxWithUBoot
from tbot import log_event
log_event.doc_tag("board_name", BOARD.name)
log_event.doc_tag("ub_prompt", UBOOT.prompt)
