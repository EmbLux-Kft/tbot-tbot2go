import contextlib
import typing
import os
import tbot
from tbot.machine import linux
from tbot.machine import board
from tbot import log_event
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
            ret = lab.exec(linux.Raw(f"PATH={self.hookscriptpath}:$PATH;PYTHONPATH={self.ubpath};{self.ubpath}/test/py/test.py --bd {lab.get_boardname} -s --build-dir {self.ubpath}"))
            if ret[0] == 1:
                retval = False
            sftp = lh.client.open_sftp()
            sftp.get(f"{self.ubpath}/test-log.html", f"{tbot.log.LOGFILE.name}-testpy-result.html")
            sftp.get(f"{self.ubpath}/test/py/multiplexed_log.css", f"{tbot.log.LOGFILE.name}-multiplexed_log.css")
            sftp.close()

            with contextlib.ExitStack() as cx:
                b = cx.enter_context(tbot.acquire_board(lh))
                b.poweroff()

        if retval != True:
            raise RuntimeError("Calling test/py failed")

        return True
