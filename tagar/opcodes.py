#!/usr/bin/python3.4

PROTOCOL_VERSION = 1.1

packet_c2s = {
    100: 'login',
    110: 'player_update',
    111: 'world_update',
}

packet_s2c = {
    200: 'handshake',
    201: 'server_message',
    210: 'player_list_update',
    211: 'world_update',
}

