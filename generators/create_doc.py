#!/usr/bin/env python3
# tbot, Embedded Automation Tool
# Copyright (C) 2018  Heiko Schocher
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Generate rst file which can be converted for example in a pdf

"""
import sys
import re
import pathlib
import string
import logparser

def main() -> None:
    """
    Generate a doucmentation in rst format. You can convert it
    for example into pdf.

    ToDo:
    - How to make chapters generic
      (add tags into rst files ?)
    """

    try:
        filename = pathlib.Path(sys.argv[1])
        log = logparser.logfile(str(filename))
        rstpath = pathlib.Path(sys.argv[2])
    except IndexError:
        sys.stderr.write(
            f"""\
\x1B[1mUsage: {sys.argv[0]} <logfile> <path2rstfiles>\x1B[0m
"""
        )
        sys.exit(1)
    except OSError:
        sys.stderr.write(
            f"""\
\x1B[31mopen failed!\x1B[0m
\x1B[1mUsage: {sys.argv[0]} <logfile> <path2rstfiles>\x1B[0m
"""
        )
        sys.exit(1)

    def tbot_write_cmd(ev, cmd_written):
        #print (" === cmd ", ev.data["cmd"])
        #print (" === typ ", ev.type)
        if cmd_written == 0:
            print("\n::\n")
        else:
            pass

        print("\t$ " + ev.data["cmd"])
        # now stdout output
        # remove ANSI escape sequences
        reasc = re.compile(r'\x1b[^m]*m')
        fix = reasc.sub('', ev.data["stdout"])
        line = "\t" + fix.replace("\n", "\n\t")
        print(line)

        cmd_written = cmd_written + 1
        return cmd_written

    def replace_tbot_tags(content):
        # TODO
        # while TBOT is running create TBOT_ tags
        # for example TBOT_BOARD_NAME
        # json file or simple text ?
        # or integrate into log ?
        #
        # also find possibility for making chapters generic
        #
        content = content.replace('TBOT_BOARD_NAME', 'testboard')
        # fix following underlines length
        # or fix underlines when found
        return content

    def write_file(ev, ending):
        fn = ev.data["docid"] + ending
        #print (" open file ", rstpath / fn)
        with open(rstpath / fn, mode="r") as f:
            content = f.read()
            content = replace_tbot_tags(content)
            print (content)

    def call_analyse(log, level):
        #print(" ====== level ===== ", level)
        cmd_written = 0
        for ev in log:
            #print (" ===== ev ", ev)
            if ev.type == ["doc", "begin"]:
                write_file(ev, "_begin.rst")
                call_analyse(log, level + 1)
                cmd_written = 0

            elif ev.type == ["doc", "end"]:
                # end
                # load content of rst end file and print
                #print (" ==== end ", ev.data["docid"])
                write_file(ev, "_end.rst")
                return level - 1

            elif ev.type == ["doc", "cmd"]:
                # load content of rst end file and print
                #print (" ==== end ", ev.data["docid"])
                write_file(ev, "_cmd.rst")
                cmd_written = 0

            elif level > 0:
                # only add cmd output, if one docid is active
                #print (" ============================== ", ev.type)
                if "cmd" in ev.type:
                    cmd_written = tbot_write_cmd(ev, cmd_written)

        return

    #print("filename ", filename)
    #print("rstpath ", rstpath)

    call_analyse(log, 0)

    print("\n")

if __name__ == "__main__":
    main()
