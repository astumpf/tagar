#!/usr/bin/python3.4
import configparser
from time import time, sleep
import sched
import threading
import socket
import uuid
import hashlib

from agarnet.buffer import BufferStruct

from .opcodes import *
from .session import *
from .player import *


class TeamServer:
    def __init__(self, address, port, password=str()):
        self.address = address
        self.port = port
        self.password = password
        self.player_list = []
        self.player_list_lock = threading.Lock()

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
                print("Rejected connection from due to wrong opcode: ", addr)
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
                print("Rejected connection from due to wrong pw: ", addr)
                sock.close()
                return

            print("Accepted connection from: ", addr)

            # init session
            id = uuid.uuid4()

            # send session id to client
            buf = BufferStruct(opcode=200)
            buf.push_null_str8(str(id))
            sock.send(buf.buffer)

            self.player_list_lock.acquire()
            self.player_list.append(Player(Session(id, sock)))
            self.player_list_lock.release()

        except socket.error:
            sock.close()

    def disconnect_client(self, player):
        player.session.disconnect()
        self.player_list.remove(player)

    def update(self):
        self.scheduler.enter(self.update_rate, 1, self.update)

        self.player_list_lock.acquire()

        try:
            player_list = BufferStruct()
            player_list_len = 0

            # handle incoming player updates and collect data for sending back to clients
            for p in self.player_list:
                try:
                    p.handle_msgs()
                    p.pack_player_update(player_list)
                    player_list_len += 1
                except socket.error:
                    self.disconnect_client(p)

            # prepare player_update_list package
            player_list_update = BufferStruct(opcode=210)
            player_list_update.push_uint32(player_list_len)
            player_list_update.append(player_list)

            # send message to all clients
            for p in self.player_list:
                try:
                    p.session.sendall(player_list_update.buffer)
                except socket.error:
                    self.disconnect_client(p)
        finally:
            self.player_list_lock.release()
