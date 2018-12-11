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
Generate a txt file which dot tool understand.

"""
import sys
import re
import pathlib
import string
import logparser

def main() -> None:
    """Generate a txt file, which dot tool understand."""

    try:
        filename = pathlib.Path(sys.argv[1])
        log = logparser.logfile(str(filename))
    except IndexError:
        sys.stderr.write(
            f"""\
\x1B[1mUsage: {sys.argv[0]} <logfile>\x1B[0m
"""
        )
        sys.exit(1)
    except OSError:
        sys.stderr.write(
            f"""\
\x1B[31mopen failed!\x1B[0m
\x1B[1mUsage: {sys.argv[0]} <logfile>\x1B[0m
"""
        )
        sys.exit(1)

    dotnr = []
    def create_knoten(name, col='black'):
        dotnr.append("el")
        nr = len(dotnr)
        tmp = str(nr) + ' [shape=record, label="' + name + '" color=' + col + '];\n'
        print(tmp)
        return nr

    def write_knotenline(last, new, color):
        tmp = str(last) + ' ->  ' + str(new) + ' [color=' + color +']\n'
        print(tmp)

    def call_anal(name, current, log):
        for ev in log:
            if ev.type == ["tc", "begin"]:
                newname = ev.data['name']
                nr = create_knoten(newname)
                write_knotenline(current, nr, 'black')
                color = call_anal(newname, nr, log)
                write_knotenline(nr, current, color)

            elif ev.type == ["tc", "end"]:
                if ev.data["success"] == True:
                    color = 'green'
                else:
                    color = 'red'
                return color
        return 'end'

    print('digraph tc_dot_output\n{\nrankdir=LR;\n')

    nr = create_knoten('main')
    end = 'go'
    while end != 'end':
        end = call_anal('main', nr, log)

    print("}\n")

if __name__ == "__main__":
    main()
