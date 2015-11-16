#!/usr/bin/python3.4
from time import sleep
import threading
import socket
import struct


class Session:
    def __init__(self, id, sock=None):
        self.id = id
        self.sock = sock
        self.recv_msgs = []
        self.is_connected = sock is not None
        self.recv_msgs_lock = threading.Lock()

        if self.is_connected:
            recv_thread = threading.Thread(target=self._recv_data)
            recv_thread.setDaemon(True)
            recv_thread.start()

        print("Started session ", self.id)

    def disconnect(self):
        if self.is_connected:
            self.is_connected = False
            self.sock.close()
            print("Closed session ", self.id)

    def _recv_data(self):
        try:
            while 1:
                msg = self.recvall()
                if msg is not None:
                    self.push_msg(msg)
                else:
                    self.disconnect()
                    return
        except socket.error:
            self.disconnect()

    def has_new_msg(self):
        return len(self.recv_msgs) > 0

    def push_msg(self, msg):
        self.recv_msgs_lock.acquire()
        self.recv_msgs.append(msg)
        self.recv_msgs_lock.release()

    def pop_msg(self):
        msg = None
        self.recv_msgs_lock.acquire()
        if self.has_new_msg():
            msg = self.recv_msgs.pop(0)
        self.recv_msgs_lock.release()
        return msg

    def sendall(self, msg):
        # Prefix each message with a 4-byte length
        msg = struct.pack('<I', len(msg)) + msg
        self.sock.sendall(msg)

    def recvall(self):
        # Read message length
        msg_len = self._recv(4)
        if not msg_len:
            return None
        msg_len = struct.unpack('<I', msg_len)[0]

        # Read the message data
        return self._recv(msg_len)

    def _recv(self, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytes()
        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data
