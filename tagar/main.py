#!/usr/bin/python3.4
import sys
import time

from .server import TeamServer


def main():
    print("Copyright (C) 2015  astumpf\n"
          "This program comes with ABSOLUTELY NO WARRANTY.\n"
          "This is free software, and you are welcome to redistribute it\n"
          "under certain conditions; see LICENSE.txt for details.\n")

    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
        print("Usage: %s [port] [password]" % sys.argv[0])
        return

    port, password, *_ = sys.argv[1:] + ([None] * 3)

    if port is None:
        port = 5555
    else:
        port = int(port)


    if password is None:
        password = str()

    server = TeamServer(port, password)

    while True:
        time.sleep(1)
