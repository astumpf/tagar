#!/usr/bin/python3.4
import sys
import configparser
import socket
from time import time, sleep
import sched
import threading
import hashlib
import random

from agarnet.buffer import BufferStruct
from agarnet.dispatcher import Dispatcher
from tagar.session import Session
from tagar.player import Player
from tagar.opcodes import *
from tagar.world import World


class TagarClient:
    def __init__(self, agar_client):
        self.agar_client = agar_client
        self.player = Player()
        self.dispatcher = Dispatcher(packet_s2c, self)
        self.player_list = {}
        self.team_world = World()
        self.session = None
        self.force_player_update = False

        config = configparser.ConfigParser({'address': 'localhost',
                                            'port': '5000',
                                            'password': '',
                                            'update_rate': '0.1'})
        config.read('tagar_client.cfg')

        self.update_rate = config.getfloat('Settings', 'update_rate')

        self.scheduler = sched.scheduler(time, sleep)
        self.scheduler.enter(self.update_rate, 1, self.recv_update)
        self.scheduler.enter(self.update_rate, 1, self.send_update)
        thread = threading.Thread(target=self.scheduler.run)
        thread.setDaemon(True)
        thread.start()

        address = config.get('Server', 'address')
        port = config.getint('Server', 'port')
        password = config.get('Server', 'password')

        self.connect(address, port, password)

    def connect(self, addr, port, password):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)

        # try to connect to server
        try:
            # Connect to server and send data
            sock.connect((addr, port))

            buf = BufferStruct(opcode=100)

            # create challenge
            rand = random.randint(1, 254)
            m = hashlib.md5()
            m.update(password.encode('utf-16'))
            m.update(str(rand).encode('utf-8'))

            # send login challenge
            buf.push_null_str8(m.hexdigest())
            buf.push_uint8(rand)
            sock.send(buf.buffer)

            # Receive data from the server
            msg = sock.recv(1024)
            if msg is None or len(msg) == 0:
                print("Connection to team server rejected!")
                return

            buf = BufferStruct(msg)

            opcode = buf.pop_uint8()

            if opcode != 200:
                sock.close()
                return

            print("Connected to tagar server: %s:%d" % (addr, port))

            self.session = Session(buf.pop_null_str8(), sock)
            self.player = Player(self.session)
            self.force_player_update = True

        except socket.error:
            print("Could not connect to tagar server: %s:%d" % (addr, port))

    def disconnect(self):
        self.session.disconnect()

    def recv_update(self):
        self.scheduler.enter(self.update_rate, 1, self.recv_update)

        if not self.session or not self.session.is_connected:
            return

        while 1:
            msg = self.session.pop_msg()
            if msg is None:
                return

            buf = BufferStruct(msg)
            while len(buf.buffer) > 0:
                self.dispatcher.dispatch(buf)

    def send_update(self):
        self.scheduler.enter(self.update_rate, 1, self.send_update)

        if not self.session or not self.session.is_connected:
            return

        # collect player info
        self.player.pre_update_player_state()
        self.player.update_player_state(sid=self.session.sid, player=self.agar_client.player, party_token=self.agar_client.server_token)

        # collect world status
        self.player.world.pre_update_world()
        self.player.world.update_world(self.agar_client.player.world.cells.copy())

        # send update
        try:
            buf = BufferStruct()

            # player status
            if self.player.has_update() or self.force_player_update:
                buf.push_uint8(110)
                self.player.pack_player_update(buf)
            self.force_player_update = False

            # world status
            if self.player.world.has_update():
                buf.push_uint8(111)
                self.player.world.pack_world_update(buf)

            if buf.buffer:
                self.session.sendall(buf.buffer)
        except socket.error:
            self.disconnect()

    def parse_player_list_update(self, buf):
        # update players
        for i in range(0, buf.pop_uint32()):
            p = Player()
            p.parse_player_update(buf)
            if str(self.session.sid) != p.sid:
                self.player_list[p.sid] = p

        # removed logged out players
        for i in range(0, buf.pop_uint32()):
            sid = buf.pop_len_str8()
            if sid in self.player_list:
                del self.player_list[sid]

    def parse_world_update(self, buf):
        self.team_world.parse_world_update(buf)
