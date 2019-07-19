import contextlib
import typing
import os
import tbot
from tbot.machine import board
from tbot import log_event
from tbot import tc

def board_power(
    lab: typing.Optional[tbot.selectable.LabHost] = None,
    board: typing.Optional[board.Board] = None,
    state = 'on',
) -> None:
    """
    power on or off the board without acquiring console.

    This is only hacky version, we should bring in this into
    tbot.
    """
    with contextlib.ExitStack() as cx:
        lh = cx.enter_context(lab or tbot.acquire_lab())

        fl = tbot.flags

        tbot.flags = {"no_console_check", "nopoweroff"}
        b = cx.enter_context(board or tbot.acquire_board(lh))

        tbot.flags = fl
        if state == 'on':
            b.poweron()
        else:
            b.poweroff()

        tbot.flags = {"no_console_check", "nopoweroff"}

@tbot.testcase
def board_power_on(
    lab: typing.Optional[tbot.selectable.LabHost] = None,
    board: typing.Optional[board.Board] = None,
) -> None:
    board_power()

@tbot.testcase
def board_power_off(
    lab: typing.Optional[tbot.selectable.LabHost] = None,
    board: typing.Optional[board.Board] = None,
) -> None:
    board_power(state = 'off')
