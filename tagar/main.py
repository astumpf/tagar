#!/usr/bin/python3.4
import sys
import configparser
from time import sleep

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

    config = configparser.ConfigParser({'address': 'localhost',
                                        'port': '5000',
                                        'password': ''})
    config.read('server.cfg')

    address = config.get('Server', 'address')
    port = config.getint('Server', 'port') if port is None else int(port)
    password = config.get('Server', 'password') if password is None else password

    server = TeamServer(address, port, password)

    while True:
        sleep(1)
