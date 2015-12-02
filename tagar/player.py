#!/usr/bin/python3.4
from copy import copy
from time import monotonic
from agarnet.buffer import BufferStruct
from agarnet.dispatcher import Dispatcher
from .world import World
from .opcodes import *


class Player:
    def __init__(self, session=None):
        self.session = session
        self.sid = str(session.sid) if session is not None else ""

        self.dispatcher = Dispatcher(packet_c2s, self)

        self.nick = str()
        self.position_x = 0.0
        self.position_y = 0.0
        self.total_mass = 0.0
        self.own_ids = set()
        self.is_alive = False
        self.party_token = str()

        self.is_updated = False

        self.world = World()

        self.last_update_time = monotonic()

    def has_update(self):
        return self.is_updated

    def pre_update_player_state(self):
        self.is_updated = False

    def update_player_state(self, sid=-1, nick='', x=0.0, y=0.0, total_mass=0.0, own_ids=set(), is_alive=False, party_token='', player=None):
        if player:
            nick = player.nick
            x, y = player.center
            total_mass = player.total_mass
            own_ids = player.own_ids
            is_alive = player.is_alive

        party_token = party_token if len(party_token) == 5 else 'FFA'
        self.is_updated = self.nick != nick or self.party_token != party_token or (self.is_alive and (self.position_x != x or self.position_y != y or self.total_mass != total_mass or self.is_alive != is_alive))
        self.sid = copy(sid)
        self.nick = copy(nick)
        self.position_x = copy(x)
        self.position_y = copy(y)
        self.total_mass = copy(total_mass)
        self.own_ids = own_ids.copy()
        self.is_alive = copy(is_alive)
        self.party_token = copy(party_token)
        self.last_update_time = monotonic()

    def handle_msgs(self):
        self.pre_update_player_state()
        self.world.pre_update_world()
        while self.session.has_new_msg():
            self.parse_msg(self.session.pop_msg())

    def parse_msg(self, msg):
        buf = BufferStruct(msg)
        while not buf.empty():
            self.dispatcher.dispatch(buf)

    def parse_player_update(self, buf):
        self.pre_update_player_state()
        self.unpack_player_update(buf)
        self.last_update_time = monotonic()

    def parse_world_update(self, buf):
        self.world.parse_world_update(buf)

    def pack_player_update(self, buf=BufferStruct()):
        buf.push_len_str8(self.sid)
        buf.push_len_str16(self.nick)
        buf.push_float32(self.position_x)
        buf.push_float32(self.position_y)
        buf.push_float32(self.total_mass)
        buf.push_uint8(len(self.own_ids))
        for cid in self.own_ids:
            buf.push_uint32(cid)
        buf.push_bool(self.is_alive)
        buf.push_null_str16(self.party_token)
        return buf

    def unpack_player_update(self, buf):
        sid = buf.pop_len_str8()
        nick = buf.pop_len_str16()
        x = buf.pop_float32()
        y = buf.pop_float32()
        total_mass = buf.pop_float32()
        own_ids = set()
        for i in range(buf.pop_uint8()):
            own_ids.add(buf.pop_uint32())
        is_alive = buf.pop_bool()
        party_token = buf.pop_null_str16()
        self.update_player_state(sid, nick, x, y, total_mass, own_ids, is_alive, party_token)
        return buf
