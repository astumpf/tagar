#!/usr/bin/python3.4
import configparser
from time import time
import sched
import threading
import socket
import uuid
import hashlib

from agarnet.buffer import BufferStruct

from .session import *
from .player import *
from .world import *


class TeamServer:
    def __init__(self, address, port, password=str()):
        self.address = address
        self.port = port
        self.password = password

        self.player_list = []
        self.logged_off_player_list = []
        self.player_list_lock = threading.Lock()

        self.world = World()
        self.world_lock = threading.Lock()

        self.force_player_list_update = False

        config = configparser.ConfigParser({'update_rate': '0.1'})
        config.read('server.cfg')

        self.update_rate = config.getfloat('Settings', 'update_rate')

        self.scheduler = sched.scheduler(time, sleep)
        self.scheduler.enter(self.update_rate, 1, self.update)
        thread = threading.Thread(target=self.scheduler.run)
        thread.setDaemon(True)
        thread.start()

        server_thread = threading.Thread(target=self.start_service)
        server_thread.setDaemon(True)
        server_thread.start()

    def __del__(self):
        self.serversocket.close()

    def start_service(self):
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        self.serversocket.bind((self.address, self.port))
        self.serversocket.listen(5)

        print("Server is listening for connections on: %s:%d" % (self.address, self.port))

        while 1:
            clientsocket, clientaddr = self.serversocket.accept()
            thread = threading.Thread(target=self.client_handler, args=(clientsocket, clientaddr))
            thread.setDaemon(True)
            thread.start()

        self.serversocket.close()

    def client_handler(self, sock, addr):
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)

            buf = BufferStruct(sock.recv(1024))
            opcode = buf.pop_uint8()

            if opcode != 100:
                print("Rejected connection from %s due to wrong opcode %d!" % (addr, opcode))
                sock.close()
                return

            # get client challenge
            hash = buf.pop_null_str8()
            rand = buf.pop_uint8()
            m = hashlib.md5()
            m.update(self.password.encode('utf-16'))
            m.update(str(rand).encode('utf-8'))

            # check if hashes are matching
            if m.hexdigest() != hash:
                msg = str("Rejected connection from %s due to wrong password!" % (addr,))
                print(msg)

                buf = BufferStruct(opcode=201)
                buf.push_len_str16(msg)
                sock.send(buf.buffer)
                sock.close()
                return

            client_version = buf.pop_len_str8()
            if client_version != str(PROTOCOL_VERSION):
                msg = str("Rejected connection from %s due to wrong protocol version (Client: %s, Server: %s)!" % (addr, client_version, str(PROTOCOL_VERSION)))
                print(msg)

                buf = BufferStruct(opcode=201)
                buf.push_len_str16(msg)
                sock.send(buf.buffer)
                sock.close()
                return

            print("Accepted connection from: ", addr)

            # init session
            id = uuid.uuid4()

            # send session id to client
            buf = BufferStruct(opcode=200)
            buf.push_len_str8(str(id))

            # add welcome message
            buf.push_uint8(201)
            buf.push_len_str16("Welcome on Tagar server at %s" % (self.address,))

            sock.send(buf.buffer)

            self.player_list_lock.acquire()
            self.world_lock.acquire()

            session = Session(id, sock)
            self.player_list.append(Player(session))
            self.force_player_list_update = True
            # TODO: Send full map

            self.player_list_lock.release()
            self.world_lock.release()

        except socket.error:
            sock.close()

    def disconnect_client(self, player):
        player.session.disconnect()
        self.player_list.remove(player)
        self.logged_off_player_list.append(player.sid)

    def update(self):
        self.scheduler.enter(self.update_rate, 1, self.update)

        self.player_list_lock.acquire()
        self.world_lock.acquire()

        try:
            # handle incoming player updates and collect data for sending back to clients
            for p in list(self.player_list):
                if not p.session.is_connected:
                    self.disconnect_client(p)
                    continue
                try:
                    p.handle_msgs()
                except socket.error:
                    self.disconnect_client(p)

            # TODO: extract method
            # update shared world
            cells = {}
            for p in self.player_list: # merge all client's world
                cells.update(p.world.cells)

            self.world.pre_update_world()
            self.world.update_world(cells)
            # TODO: end extract method

            # prepare broadcast update
            buf = BufferStruct()

            # prepare player_update_list package
            self.pack_player_list(buf, self.force_player_list_update)
            self.logged_off_player_list = []
            self.force_player_list_update = False

            # TODO: send full map when player has just logged in
            # prepare world_update package
            self.pack_world_update(buf)

            # send message to all clients
            if buf.buffer:
                for p in self.player_list:
                    try:
                        p.session.sendall(buf.buffer)
                    except socket.error:
                        self.disconnect_client(p)
        finally:
            self.player_list_lock.release()
            self.world_lock.release()

    def pack_player_list(self, buf=BufferStruct(), force_update=False):
        # prepare player_update_list package
        updated_players = [p for p in self.player_list if p.has_update() or force_update]
        if not updated_players and not self.logged_off_player_list:
            return buf

        buf.push_uint8(210)

        # add player update
        buf.push_uint32(len(updated_players))
        for p in updated_players:
            p.pack_player_update(buf)

        # add logged out players
        buf.push_uint32(len(self.logged_off_player_list))
        for sid in self.logged_off_player_list:
            buf.push_len_str8(sid)
        return buf

    def pack_world_update(self, buf=BufferStruct()):
        if self.world.has_update():
            buf.push_uint8(211)
            self.world.pack_world_update(buf)
        return buf
