import typing
import tbot
from tbot.machine import channel, board, linux
import generic as ge
from tbot.tc import git

if tbot.selectable.LabHost.name == "tbot2go":
    # Use lab specific config
    import raspi as lab
else:
    raise NotImplementedError("Board not available on this labhost!")

class bbb(lab.Board):
    name = "bbb"
    connect_wait = 0.0

ub_env = [
]

class bbbUBootBuilder(lab.UBootBuilder):
    name = "bbb-builder"
    defconfig = "am335x_evm_defconfig"
    toolchain = "linaro-gnueabi"
    remote = "git@gitlab.denx.de:u-boot/u-boot.git"

    testpy_boardenv = r"""# Config for BBB
# Set sleep time and margin
env__sleep_time = 20
env__sleep_margin = 2
"""

    def do_checkout(self, target: linux.Path, clean: bool, rev: typing.Optional[str]) -> git.GitRepository:
        branch = "master"
        return git.GitRepository(
            target=target, url=self.remote, clean=clean, rev=branch
        )

    def do_patch(self, repo: git.GitRepository) -> None:
        repo.am(linux.Path(repo.host, "/work/hs/tbot2go/patches/bbb"))

class bbbUBoot(lab.UBootMachine):
    name = "bbb-uboot"
    prompt = "=> "
    build = bbbUBootBuilder()

    if "bootmodesd" in tbot.flags:
        #autoboot_prompt = 'Press SPACE to abort autoboot in'
        #autoboot_prompt = 'Hit any key to stop autoboot'
        #autoboot_keys = ' '
        autoboot_prompt = None
    else:
        #autoboot_prompt = 'Hit any key to stop autoboot'
        #autoboot_keys = ' '
        autoboot_prompt = None

    def do_set_env( 
        self, ub: board.UBootShell
    ) -> bool:
        ub.env("serverip", tbot.selectable.LabHost.serverip)
        ub.env("netmask", "255.255.255.0")
        ub.env("ipaddr", tbot.selectable.LabHost.boardip["bbb"])
        ub.env("load_addr_r", "81000000")
        ub.env("cmp_addr_r", "82000000")
        tftpboardname = "bbb"
        ub_load_board_env_subdir = tbot.selectable.LabHost.ub_load_board_env_subdir
        #nfs_subdir = ge.get_path(tbot.selectable.LabHost.nfs_root) + "/bbb"
        nfs_subdir = "/work/tbot2go/tbot/nfs/bbb"
        ub.env("mlofile", f"{tftpboardname}/{ub_load_board_env_subdir}/MLO")
        ub.exec0("setenv", "load_mlo", "tftp", linux.special.Raw("${load_addr_r}"), linux.special.Raw("${mlofile}"))
        ub.env("ubfile", f"{tftpboardname}/{ub_load_board_env_subdir}/u-boot.img")
        ub.exec0("setenv", "load_uboot", "tftp", linux.special.Raw("${load_addr_r}"), linux.special.Raw("${ubfile}"))
        ub.exec0(linux.special.Raw('setenv upd_mlo mmc dev 0\;fatwrite mmc 0:1 \${load_addr_r} MLO \${filesize}'))
        ub.exec0(linux.special.Raw('setenv upd_uboot mmc dev 0\;fatwrite mmc 0:1 \${load_addr_r} u-boot.img \${filesize}'))
        ub.exec0(linux.special.Raw('setenv cmp_mlo fatload mmc 0:1 \${load_addr_r} MLO \${filesize}\;tftp \${cmp_addr_r} \${mlofile}\;cmp.b \${load_addr_r} \${cmp_addr_r} \${filesize}'))
        ub.exec0(linux.special.Raw('setenv cmp_uboot fatload mmc 0:1 \${load_addr_r} u-boot.img\;tftp \${cmp_addr_r} \${ubfile}\;cmp.b \${load_addr_r} \${cmp_addr_r} \${filesize}'))
        ub.exec0(linux.special.Raw('setenv tbot_upd_uboot run load_uboot\;run upd_uboot_emmc'))
        ub.exec0(linux.special.Raw('setenv tbot_cmp_uboot run cmp_uboot_emmc'))
        ub.exec0(linux.special.Raw('setenv tbot_upd_spl run load_mlo\;run upd_mlo_emmc'))
        ub.exec0(linux.special.Raw('setenv tbot_cmp_spl run cmp_mlo_emmc'))
        ub.exec0(linux.special.Raw('setenv upd_mlo_emmc mmc dev 1\;mmc write \${load_addr_r} 100 100'))
        ub.exec0(linux.special.Raw('setenv upd_uboot_emmc mmc dev 1\;mmc erase 400 400\;mmc write \${load_addr_r} 300 600'))
        ub.exec0(linux.special.Raw('setenv cmp_mlo_emmc mmc read \${cmp_addr_r} 100 100\;cmp.b \${load_addr_r} \${cmp_addr_r} \${filesize}'))
        ub.exec0(linux.special.Raw('setenv cmp_uboot_emmc mmc read \${cmp_addr_r} 300 600\;cmp.b \${load_addr_r} \${cmp_addr_r} \${filesize}'))
        ub.exec0(linux.special.Raw('setenv console ttyO0,115200n8'))
        ub.exec0(linux.special.Raw('setenv console ttyS0,115200n8'))
        ub.env("bootfile", f"{tftpboardname}/{ub_load_board_env_subdir}/zImage")
        ub.env("fdtfile", f"{tftpboardname}/{ub_load_board_env_subdir}/am335x-boneblack.dtb")
        ub.exec0(linux.special.Raw('setenv netmmcboot echo Booting from network ... with mmcargs ...\; setenv autoload no\; run netloadimage\; run netloadfdt\; run args_mmc\; bootz \${loadaddr} - \${fdtaddr}'))
        ub.env("netdev", "eth0")
        ub.env("hostname", "bbb")
        ub.exec0(linux.special.Raw('setenv addip setenv bootargs \${bootargs} ip=\${ipaddr}:\${serverip}:\${gatewayip}:\${netmask}:\${hostname}:\${netdev}::off panic=1'))
        ub.exec0(linux.special.Raw('setenv addcon setenv bootargs \${bootargs} console=\${console}'))
        ub.exec0(linux.special.Raw('setenv addmisc setenv bootargs \${bootargs} loglevel=8'))
        ub.exec0(linux.special.Raw('setenv addmtd setenv bootargs \${bootargs} \${mtdparts}'))
        ub.env("rootpath", nfs_subdir)
        ub.env("nfsopts", "nfsvers=3 nolock rw")
        ub.exec0(linux.special.Raw('setenv nfsargs setenv bootargs \${bootargs} root=/dev/nfs rw nfsroot=\${serverip}:\${rootpath},\${nfsopts}'))
        ub.exec0(linux.special.Raw('setenv net_nfs run netloadimage\; run netloadfdt\;run nfsargs addcon addip addmtd addmisc\;bootz \${loadaddr} - \${fdtaddr}'))
        ub.exec0(linux.special.Raw('setenv sdloadk ext2load mmc 0:2 \${loadaddr} /boot/zImage'))
        ub.exec0(linux.special.Raw('setenv sdloadfdt ext2load mmc 0:2 \${fdtaddr} /boot/am335x-boneblack.dtb'))
        ub.exec0(linux.special.Raw('setenv sd_sd run sdloadk\; run sdloadfdt\;run args_mmc addip addmtd addmisc\;bootz \${loadaddr} - \${fdtaddr}'))
        for env in ub_env:
            ub.env(env["name"], env["val"])

BOARD = bbb
UBOOT = bbbUBoot
from tbot import log_event
log_event.doc_tag("board_name", BOARD.name)
log_event.doc_tag("ub_prompt", UBOOT.prompt)
