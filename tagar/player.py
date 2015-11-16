#!/usr/bin/python3.4
from time import monotonic
from agarnet.buffer import BufferStruct
from agarnet.dispatcher import Dispatcher
from .world import World
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

        self.world = World()

        self.last_update_time = monotonic()

    def update_player_state(self, player, party_token):
        self.nick = player.nick
        self.position_x, self.position_y = player.center
        self.mass = player.total_mass
        self.is_alive = player.is_alive
        self.party_token = party_token if len(party_token) == 5 else 'FFA'
        self.last_update_time = monotonic()

    def handle_msgs(self):
        while self.session.has_new_msg():
            self.parse_msg(self.session.pop_msg())

    def parse_msg(self, msg):
        buf = BufferStruct(msg)
        while len(buf.buffer) > 0:
            self.dispatcher.dispatch(buf)

    def parse_player_update(self, buf):
        self.unpack_player_update(buf)
        self.last_update_time = monotonic()

    def parse_world_update(self, buf):
        self.world.parse_world_update(buf)

    def pack_player_update(self, buf=BufferStruct()):
        buf.push_null_str8(self.id)
        buf.push_null_str16(self.nick)
        buf.push_float32(self.position_x)
        buf.push_float32(self.position_y)
        buf.push_float32(self.mass)
        buf.push_bool(self.is_alive)
        buf.push_null_str16(self.party_token)
        return buf

    def unpack_player_update(self, buf):
        self.id = buf.pop_null_str8()
        self.nick = buf.pop_null_str16()
        self.position_x = buf.pop_float32()
        self.position_y = buf.pop_float32()
        self.mass = buf.pop_float32()
        self.is_alive = buf.pop_bool()
        self.party_token = buf.pop_null_str16()
        return buf
