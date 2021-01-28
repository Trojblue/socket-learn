#!/usr/bin/python
# This is a simple port-forward / proxy, written using only the default python
# library. If you want to make a suggestion or fix something you can contact-me
# at voorloop_at_gmail.com
# Distributed over IDC(I Don't Care) license

# https://gist.github.com/darkwave/52842722c0c451807df4

import socket
import select
import time
import sys

# Changing the buffer_size and delay, you can improve the speed and bandwidth.
# But when buffer get to high or delay go too down, you can broke things
buffer_size = 4096
delay = 0.0001
forward_to = ('www.example.org', 80)



def forward_connection(host, port):
    """establish connection to the remote<host>:<port>
    return: socket object
    """
    fwd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        fwd_sock.connect((host, port))
        return fwd_sock
    except Exception as e:
        print(e)
        return False


class TheServer:

    def __init__(self, port):
        self.s = None
        self.channel = {}
        self.input_list = []
        self.host = 'localhost'
        self.init_sock(port)

    def init_sock(self, port):
        # AF_INET: ipv4;  SOCK_STREAM: tcp
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # re-use socket
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, port))

        # 前最大接收200个unaccepted connections (等待queue)
        self.server.listen(200)


    def start(self):
        self.input_list.append(self.server)
        while 1:
            time.sleep(delay)

            in_ready = select.select(self.input_list, [], [])[0]
            for curr_sock in in_ready:
                self.s = curr_sock

                if self.s == self.server:
                    self.on_accept()    # 连接
                    break

                self.data = self.s.recv(buffer_size)    # 接受数据
                if len(self.data) == 0:
                    self.on_close()
                    break
                else:
                    self.on_recv()      # 发回client

    def on_accept(self):
        fwd_host, fwd_port = forward_to[0], forward_to[1]

        # connect到remote
        fwd_sock = forward_connection(fwd_host, fwd_port)
        test_data_2 = (b"GET / HTTP/1.1\r\nHost: %s\r\n"
                             b"Accept: text/html\r\nConnection: close\r\nuser-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             b"Chrome/88.0.4324.104 Safari/537.36\r\n\r\n" % b'www.example.org')
        fwd_sock.sendall(test_data_2)

        # accept到client
        client_sock, client_addr = self.server.accept()
        client_header = client_sock.recv(4096)

        if fwd_sock:
            print(client_addr, "has connected")
            self.input_list.append(client_sock)
            self.input_list.append(fwd_sock)
            self.channel[client_sock] = fwd_sock
            self.channel[fwd_sock] = client_sock
        else:
            print("error: cannot connect to remote")
            client_sock.close()

    def on_close(self):
        print(self.s.getpeername(), "has disconnected")
        # remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[self.s]

    def on_recv(self):
        data = self.data
        # here we can parse and/or modify the data before send forward
        print(data)

        # test_data_2 = (b"GET / HTTP/1.1\r\nHost: %s\r\n"
        #                      b"Accept: text/html\r\nConnection: close\r\nuser-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        #                      b"Chrome/88.0.4324.104 Safari/537.36\r\n\r\n" % b'www.example.org')
        self.channel[self.s].send(data)


if __name__ == '__main__':
    server = TheServer(8890)
    try:
        print("server running...")
        server.start()
    except KeyboardInterrupt:
        print("Ctrl C - Stopping server")
        sys.exit(1)
