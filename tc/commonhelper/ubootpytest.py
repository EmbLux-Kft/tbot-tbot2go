import contextlib
import typing
import os
import tbot
from tbot.machine import linux
from tbot.machine import board
from tbot import log_event
from tbot import tc
import tbot.tc.shell
import generic as ge

class Ubootpytest:
    """
    call test.py from u-boot test/py/test.py

    #PATH=/home/hs/testframework/hook-scripts:$PATH;PYTHONPATH=/work/hs/tbot//u-boot-at91sam9g45;./test/py/test.py --bd corvus -s --build-dir .

    :param hookscriptpath path:
    :param ubpath path:
    """
    def __init__(self, hookscriptpath, ubpath):
        self.hookscriptpath = hookscriptpath
        self.ubpath = ubpath

    @tbot.testcase
    def ub_call_test_py(
        self,
        lab: typing.Optional[linux.LabHost],
    ) -> bool:
        retval = True
        with lab or tbot.acquire_lab() as lh:
            with contextlib.ExitStack() as cx:
                b = cx.enter_context(tbot.acquire_board(lh))
                ub = cx.enter_context(tbot.acquire_uboot(b))
                ub.exec0("echo", "start with test from u-boot sources")

            # now board should be off and console free
            with lh.subshell():
                old_path = lh.env("PATH")
                lh.env("PATH", f"{self.hookscriptpath}:{old_path}")
                lh.env("PYTHONPATH", self.ubpath)

                ret = lh.exec(f"{self.ubpath}/test/py/test.py", "--bd", lab.get_boardname, "-s", "--build-dir", self.ubpath)

            if ret[0] == 1:
                retval = False

            log_event.doc_end("ub_call_test_py")

            with linux.lab.LocalLabHost() as lo:
                tbot.log.message("Fetching test log ...")
                # Copy test-log
                ubpath = linux.Path(lh, self.ubpath)
                for p_remote, p_local in [
                    (ubpath / "test-log.html", linux.Path(lo, f"{tbot.log.LOGFILE.name}-testpy-result.html")),
                    (ubpath / "test" / "py" / "multiplexed_log.css", linux.Path(lo, f"{tbot.log.LOGFILE.name}-multiplexed_log.css")),
                ]:
                    tc.shell.copy(p_remote, p_local)

            with contextlib.ExitStack() as cx:
                b = cx.enter_context(tbot.acquire_board(lh))
                b.poweroff()

        if retval != True:
            raise RuntimeError("Calling test/py failed")

        return True
