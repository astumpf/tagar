#!/usr/bin/python3.4
from time import monotonic
from agarnet.buffer import BufferStruct
from agarnet.dispatcher import Dispatcher
from .opcodes import *


class Player:
    def __init__(self, session=None):
        self.session = session
        self.id = str(session.id) if session is not None else ""

        self.dispatcher = Dispatcher(packet_c2s, self)

        self.nick = str()
        self.position_x = 0.0
        self.position_y = 0.0
        self.mass = 0.0
        self.is_alive = False
        self.party_token = str()

        self.last_update_time = monotonic()

    def handle_msgs(self):
        while self.session.has_new_msg():
            self.parse_msg(self.session.pop_msg())

    def parse_msg(self, msg):
        buf = BufferStruct(msg)
        while len(buf.buffer) > 0:
            self.dispatcher.dispatch(buf)

    def parse_player_update(self, buf):
        self.id = buf.pop_null_str8()
        self.nick = buf.pop_null_str16()
        self.position_x = buf.pop_float32()
        self.position_y = buf.pop_float32()
        self.mass = buf.pop_float32()
        self.is_alive = buf.pop_bool()
        self.party_token = buf.pop_null_str16()
        self.last_update_time = monotonic()

    def pack_player_update(self, buf = BufferStruct()):
        buf.push_null_str8(self.id)
        buf.push_null_str16(self.nick)
        buf.push_float32(self.position_x)
        buf.push_float32(self.position_y)
        buf.push_float32(self.mass)
        buf.push_bool(self.is_alive)
        buf.push_null_str16(self.party_token)
