import contextlib
import typing
import tbot
from tbot.machine import linux
import generic as ge

class Yocto:
    """class for yocto tasks

    yoctype : type of yocto repo
              currently only "repo" supported, which means use repo tool from google:
              https://source.android.com/setup/build/downloading#installing-repo
              for getting all the sources for build.

    directory structure on build machein "ma":

    ma.workdir / tbot.selectable.Board.name / self.yocto_type   / tbot.selectable.Board.name / "build_" + tbot.selectable.Board.name /
               | ge.get_board_workdir       | get_yocto_workdir | get_repodir                | repo_get_builddir                     |
               | ge.cd_board_workdir        | cd_yocto_workdir  | cd2repo                    | repo_cd_builddir                      |
               |                            |                   | repodirname

    get deploy directory: repo_get_deploydir()
    repo_get_builddir() / repo_get_deploydir_name ()
                          "tmp/deploy/images/" + tbot.selectable.Board.name
    """

    def __init__(self, yoctype, repodirname):
        self.yocto_type = yoctype
        self.repodirname = repodirname
        self.repo_path = '/home/hs/bin/repo'
        self.tested = False

    @tbot.testcase
    def get_yocto_workdir(self, ma) -> str:
        p2 = ge.get_board_workdir(ma)
        # may we add here other options without repo
        p2 = p2 / self.yocto_type
        if not p2.exists():
            ma.exec0("mkdir", "-p", p2)
        return p2

    @tbot.testcase
    def cd_yocto_workdir(self, ma) -> str:
        p = self.get_yocto_workdir(ma)
        ma.exec0("cd", p)
        return p

    @tbot.testcase
    def repo_exist(self, ma) -> bool:
        if self.yocto_type != 'repo':
            raise RuntimeError("not configured for " + self.yocto_type)

        if self.tested == False:
            ma.exec0(linux.Raw("export PATH=$PATH:" + self.repo_path))
            ma.exec0(linux.Raw("printenv PATH"))
            self.tested = True

        p = self.cd_yocto_workdir(ma)
        p = p / ".repo"
        if p.exists():
            return True
        return False

    @tbot.testcase
    def get_repodir(self, ma) -> str:
        p = self.cd_yocto_workdir(ma)
        # may we need this configurable
        p = p / self.repodirname
        if p.exists():
            return p

    @tbot.testcase
    def cd2repo(self, ma) -> str:
        p = self.get_repodir(ma)
        if p.exists():
            ma.exec0("cd", p)
            return p
        raise RuntimeError("repo dir missing")

    @tbot.testcase
    def repo_get_builddir_name(self, ma) -> str:
        bd = "build_" + tbot.selectable.Board.name
        return bd

    @tbot.testcase
    def repo_get_builddir(self, ma) -> str:
        bd = self.repo_get_builddir_name(ma)
        p = self.get_repodir(ma)
        p = p / bd
        return p

    @tbot.testcase
    def repo_cd_builddir(self, ma) -> str:
        p = self.repo_get_builddir(ma)
        if p.exists():
            ma.exec0("cd", p)
            return p
        raise RuntimeError("repo build dir missing")

    @tbot.testcase
    def repo_get_deploydir_name(self, ma) -> str:
        bd = "tmp/deploy/images/" + tbot.selectable.Board.name
        return bd

    @tbot.testcase
    def repo_get_deploydir(self, ma) -> str:
        p = self.repo_get_builddir(ma)
        n = self.repo_get_deploydir_name(ma)
        p = p / n
        return p

    # commands
    @tbot.testcase
    def repo_init(self, ma, u, m, b) -> bool:
        if self.repo_exist(ma):
            return True
        ma.exec0("repo", "init", "-u", u, "-m", m, "-b", b)
        return True

    @tbot.testcase
    def repo_sync(self, ma) -> bool:
        if not self.repo_exist(ma):
            return False
        ma.exec0("repo", "sync")
        return True

    @tbot.testcase
    def repo_config(self, ma) -> str:
        if not self.repo_exist(ma):
            return False
        p = self.cd2repo(ma)
        bd = self.repo_get_builddir_name(ma)
        p2 = p / bd
        if p2.exists():
            ma.exec0("source", "oe-init-build-env", bd)
        else:
            return False
