#!/usr/bin/python3.4

packet_c2s = {
    100: 'login',
    110: 'player_update',
    111: 'world_update',
}

packet_s2c = {
    200: 'handshake',
    210: 'player_list_update',
    211: 'world_update',
}

