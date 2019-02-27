import contextlib
import typing
import os
import tbot
from tbot.machine import linux
import generic as ge

class Yocto:
    """class for yocto tasks

    yoctype : type of yocto repo
              currently only "repo" supported, which means use repo tool from google:
              https://source.android.com/setup/build/downloading#installing-repo
              for getting all the sources for build.

    directory structure on build machine "ma":

    cfg : configuration dictionary

    workdir structure:

    ma.workdir / tbot.selectable.Board.name / self.yocto_type   / tbot.selectable.Board.name / "build_" + tbot.selectable.Board.name /
               | ge.get_board_workdir       | get_yocto_workdir | get_repodir                | repo_get_builddir                     |
               | ge.cd_board_workdir        | cd_yocto_workdir  | cd2repo                    | repo_cd_builddir                      |
               |                            |                   | repodirname

    get deploy directory: repo_get_deploydir()
    repo_get_builddir() / repo_get_deploydir_name ()
                          "tmp/deploy/images/" + tbot.selectable.Board.name

    configuration

    yo_cfg ={}
    yo_cfg["u"] = "ssh://git@gitlab.denx.de/ssi/cuby-manifest.git"
    yo_cfg["m"] = "manifest-denx-20180202.xml"
    yo_cfg["b"] = "denx-pyro"
    yo_cfg["templateconf"] = "TEMPLATECONF=meta-cuby-denx/conf/samples/"
    yo_cfg["autosamplepath"] = "meta-cuby-denx/conf/samples"
    yo_cfg["bitbake_targets"] = ["cuby-image", "qt-cuby -c do_populate_sdk"]
    yo_cfg["priv_layer"] = "url to private layer"
    yo_cfg["priv_layer_branch"] = "branch which get checked out"
    
    """

    def __init__(self, yoctype, repodirname, cfg):
        self.yocto_type = yoctype
        self.repodirname = repodirname
        self.tested = False
        self.cfg = cfg

    @tbot.testcase
    def yo_repo_install(
        self,
        lab: typing.Optional[linux.LabHost] = None,
        build: typing.Optional[linux.BuildMachine] = None,
    ) -> str:
        with lab or tbot.acquire_lab() as lh:
            with build or lh.build() as bh:
                self.cd_yocto_workdir(bh)
                self.repo_init(bh, self.cfg["u"], self.cfg["m"], self.cfg["b"])
                self.repo_sync(bh, check=False)
                p = self.cd2repo(bh)
                return p

    @tbot.testcase
    def yo_repo_sync(
        self,
        lab: typing.Optional[linux.LabHost] = None,
        build: typing.Optional[linux.BuildMachine] = None,
    ) -> None:
        with lab or tbot.acquire_lab() as lh:
            with build or lh.build() as bh:
                self.cd_yocto_workdir(bh)
                self.repo_sync(bh)

    @tbot.testcase
    def yo_repo_config(
        self,
        lab: typing.Optional[linux.LabHost] = None,
        build: typing.Optional[linux.BuildMachine] = None,
    ) -> None:
        with lab or tbot.acquire_lab() as lh:
            with build or lh.build() as bh:
                try:
                    p = self.cd2repo(bh)
                except:
                    p = self.yo_repo_install(lh, bh)

                if self.cfg["priv_layer"] != None:
                    if isinstance(self.cfg["priv_layer"], str):
                        self.cfg["priv_layer"] = [self.cfg["priv_layer"]]
                    if isinstance(self.cfg["priv_layer_branch"], str):
                        self.cfg["priv_layer_branch"] = [self.cfg["priv_layer_branch"]]

                    i = 0
                    for layer in self.cfg["priv_layer"]:
                        basename = os.path.basename(layer)
                        if '.' in basename:
                            basename = basename.split('.')[0]
                        p2 = p / basename
                        if p2.exists():
                            # get newest commit
                            bh.exec0("cd", p2)
                            bh.exec0("git", "pull")
                            bh.exec0("cd", p)
                        else:
                            if self.cfg["priv_layer_branch"][i] != None:
                                bh.exec0("git", "clone", "-b", self.cfg["priv_layer_branch"][i], layer)
                            else:
                                bh.exec0("git", "clone", layer)
                        i += 1

                p = self.cd2repo(bh)
                bd = self.repo_get_builddir_name(bh)
                p2 = p / bd
                if p2.exists() == False:
                    bd = self.repo_get_builddir_name(bh)
                    bh.exec0(self.cfg["templateconf"], "source", "oe-init-build-env", bd)
                    if self.cfg["autosamplepath"] != None:
                        bh.exec0("cp", p / self.cfg["autosamplepath"] / "auto.conf.sample", "conf/auto.conf")
                        # set DL_DIR specific for build host
                        try:
                            if bh.dl_dir:
                                ge.lx_replace_line_in_file(bh, "conf/auto.conf", "DL_DIR", 'DL_DIR="' + bh.dl_dir + '"')
                        except:
                            pass
                        # set SSTATE_DIR specific for build host
                        try:
                            if bh.sstate_dir:
                                ge.lx_replace_line_in_file(bh, "conf/auto.conf", "SSTATE_DIR", 'SSTATE_DIR="' + bh.sstate_dir + '/' + tbot.selectable.Board.name + '"')
                        except:
                            pass
                else:
                    bd = self.repo_get_builddir_name(bh)
                    bh.exec0("source", "oe-init-build-env", bd)

    @tbot.testcase
    def yo_repo_build(
        self,
        lab: typing.Optional[linux.LabHost] = None,
        build: typing.Optional[linux.BuildMachine] = None,
    ) -> None:
        with lab or tbot.acquire_lab() as lh:
            with build or lh.build() as bh:
                if "nosync" not in tbot.flags:
                    self.yo_repo_sync(lh, bh)
                self.yo_repo_config(lh, bh)
                with bh.subshell():
                    bh.env("MACHINE", tbot.selectable.Board.name)

                    for name in self.cfg["bitbake_targets"]:
                        bh.exec0("bitbake", name)

    @tbot.testcase
    def get_yocto_workdir(
        self,
        ma: typing.Optional[linux.LinuxMachine],
    ) -> str:
        p2 = ge.get_board_workdir(ma)
        # may we add here other options without repo
        p2 = p2 / self.yocto_type
        if not p2.exists():
            ma.exec0("mkdir", "-p", p2)
        return p2

    @tbot.testcase
    def cd_yocto_workdir(
        self,
        ma: typing.Optional[linux.LinuxMachine],
    ) -> str:
        p = self.get_yocto_workdir(ma)
        ma.exec0("cd", p)
        return p

    @tbot.testcase
    def repo_exist(
        self,
        ma: typing.Optional[linux.LinuxMachine],
    ) -> bool:
        if self.yocto_type != 'repo':
            raise RuntimeError("not configured for " + self.yocto_type)

        if self.tested == False:
            try:
                old_path = ma.env("PATH")
                ma.env("PATH", f"{old_path}:{ma.repo_path}")
                ma.env("PATH")
            except:
                pass
            self.tested = True

        p = self.get_yocto_workdir(ma)
        p = p / ".repo"
        if p.exists():
            return True
        return False

    @tbot.testcase
    def get_repodir(
        self,
        ma: typing.Optional[linux.LinuxMachine],
    ) -> str:
        p = self.cd_yocto_workdir(ma)
        # may we need this configurable
        p = p / self.repodirname
        if p.exists():
            return p

    @tbot.testcase
    def cd2repo(
        self,
        ma: typing.Optional[linux.LinuxMachine],
    ) -> str:
        p = self.get_repodir(ma)
        if p.exists():
            ma.exec0("cd", p)
            return p
        raise RuntimeError("repo dir missing")

    @tbot.testcase
    def repo_get_builddir_name(
        self,
        ma: typing.Optional[linux.LinuxMachine],
    ) -> str:
        bd = "build_" + tbot.selectable.Board.name
        return bd

    @tbot.testcase
    def repo_get_builddir(
        self,
        ma: typing.Optional[linux.LinuxMachine],
    ) -> str:
        bd = self.repo_get_builddir_name(ma)
        p = self.get_repodir(ma)
        p = p / bd
        return p

    @tbot.testcase
    def repo_cd_builddir(
        self,
        ma: typing.Optional[linux.LinuxMachine],
    ) -> str:
        p = self.repo_get_builddir(ma)
        if p.exists():
            ma.exec0("cd", p)
            return p
        raise RuntimeError("repo build dir missing")

    @tbot.testcase
    def repo_get_deploydir_name(
        self,
        ma: typing.Optional[linux.LinuxMachine],
        extension: str = None,
    ) -> str:
        bd = "tmp/deploy/images/" + tbot.selectable.Board.name
        if extension != None:
            bd += extension
        return bd

    @tbot.testcase
    def repo_get_deploydir(
        self,
        ma: typing.Optional[linux.LinuxMachine],
        extension: str = None,
    ) -> str:
        p = self.repo_get_builddir(ma)
        n = self.repo_get_deploydir_name(ma, extension)
        p = p / n
        return p

    # commands
    @tbot.testcase
    def repo_init(
        self,
        ma: typing.Optional[linux.LinuxMachine],
        u,
        m,
        b,
    ) -> bool:
        if self.repo_exist(ma):
            return True
        ma.exec0("repo", "init", "-u", u, "-m", m, "-b", b)
        return True

    @tbot.testcase
    def repo_sync(
        self,
        ma: typing.Optional[linux.LinuxMachine],
        check=True
    ) -> bool:
        ret = self.repo_exist(ma)
        self.cd_yocto_workdir(ma)
        if check and ret == False:
            return False
        ma.exec0("repo", "sync")
        return True

    @tbot.testcase
    def repo_config(
        self,
        ma: typing.Optional[linux.LinuxMachine],
    ) -> str:
        if not self.repo_exist(ma):
            return False
        p = self.cd2repo(ma)
        bd = self.repo_get_builddir_name(ma)
        p2 = p / bd
        if p2.exists():
            ma.exec0("source", "oe-init-build-env", bd)
        else:
            return False

FLAGS = {
        "nosync":"build without repo sync",
        }
