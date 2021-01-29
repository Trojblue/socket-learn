import signal
import socket
import threading
import time
from part3 import *


class Header:
    """
    用于读取和解析头信息
    """

    def __init__(self, conn):
        self._method = None
        header = b''
        try:
            while 1:
                data = conn.recv(4096)
                header = b"%s%s" % (header, data)
                if header.endswith(b'\r\n\r\n') or (not data):
                    break
        except:
            pass
        self._header = header
        self.header_list = header.split(b'\r\n')
        self._host = None
        self._port = None

    def get_method(self):
        """
        获取请求方式
        :return:
        """
        if self._method is None:
            self._method = self._header[:self._header.index(b' ')]
        return self._method

    def get_host_info(self):
        """
        获取目标主机的ip和端口
        :return:
        """
        if self._host is None:
            method = self.get_method()
            line = self.header_list[0].decode('utf8')
            if method == b"CONNECT":
                host = line.split(' ')[1]
                if ':' in host:
                    host, port = host.split(':')
                else:
                    port = 443
            else:
                for i in self.header_list:
                    if (i.startswith(b"Host:") or i.startswith(b"host:")):
                        host = i.split(b" ")
                        if len(host) < 2:
                            continue
                        host = host[1].decode('utf8')
                        break
                else:
                    host = line.split('/')[2]
                if ':' in host:
                    host, port = host.split(':')
                else:
                    port = 80
            self._host = host
            self._port = int(port)
        return self._host, self._port

    @property
    def data(self):
        """
        返回头部数据
        :return:
        """
        return self._header

    def is_ssl(self):
        """
        判断是否为 https协议
        :return:
        """
        if self.get_method() == b'CONNECT':
            return True
        return False

    def __repr__(self):
        return str(self._header.decode("utf8"))


class Server:
    def __init__(self, config):
        # Shutdown on Ctrl+C
        signal.signal(signal.SIGINT, self.shutdown)

        # Create a TCP socket
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Re-use the socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # bind the socket to a public host, and a port
        self.serverSocket.bind((config['HOST_NAME'], config['BIND_PORT']))

        self.serverSocket.listen(10)  # become a server socket
        self.__clients = {}

    def start(self):
        while True:
            # Establish the connection
            (clientSocket, client_address) = self.serverSocket.accept()

            d = threading.Thread(name=self._getClientName(client_address),
                                 target=self.proxy_thread, args=(clientSocket, client_address))
            d.setDaemon(True)
            d.start()


def get_webpage():
    import socket

    request = b"GET /~ylzhang/ HTTP/1.1\r\nHost: cs.toronto.edu\r\n" \
                  b"Accept: text/html\r\nConnection: close\r\nuser-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                  b"Chrome/88.0.4324.104 Safari/537.36\r\n\r\n"

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("www.cs.toronto.edu", 80))
    s.send(request)
    result = s.recv(10000)
    while (len(result) > 0):
        print(result)
        result = s.recv(10000)

def get_webpage2():
    import socket
    request = b"GET ~bonner/courses/2020f/csc311/ HTTP/1.1\nHost: www.cs.toronto.edu\n\n"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("www.cs.toronto.edu", 80))
    s.send(request)
    result = s.recv(10000)
    while (len(result) > 0):
        print(result)
        result = s.recv(10000)

def socket_get():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        # s.connect(("www.example.org", 80))
        # s.sendall(b"GET / HTTP/1.1\r\nHost: example.org\r\nAccept: text/html\r\nConnection: close\r\n\r\n")

        # s.connect(("www.cs.torornto.edu/~ylzhang", 80))
        # s.sendall(b"GET / HTTP/1.1\r\nHost: cs.torornto.edu\r\nAccept: text/html\r\nConnection: close\r\n\r\n")

        # s.connect(("localhost", 5555))
        # s.sendall(b"GET / HTTP/1.1\r\nHost: example.org\r\nAccept: text/html\r\nConnection: close\r\n\r\n")

        s.connect(("www.example.org", 80))
        s.sendall(b"GET / HTTP/1.1\r\nHost: example.org\r\nAccept: text/html\r\nConnection: close\r\n\r\n")

        while True:

            data = s.recv(1024)

            if not data:
                break

            print(data.decode())


def socket_transfer():
    """从一个remote GET到信息, 然后转发给另一个
    """
    client = ("localhost", 10000)
    remote = ("www.example.org", 80)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s_client:

        s_client.connect(client)  # client

        s_remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_remote.connect(remote)
        s_remote.sendall(b"GET / HTTP/1.1\r\nHost: example.org\r\nAccept: text/html\r\nConnection: close\r\n\r\n")

        while True:

            data = s_remote.recv(1024)

            if not data:
                break

            print(data.decode())
            s_client.sendall(data)


def accept_connections():
    """在chrome访问<localhost:8888>,
    发送<remote>

    丑陋, but it works
    换成百度也可以用
    """
    print("server starting....")
    server_config = ("localhost", 8888)
    remote = ("www.example.org", 80)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(server_config)
    server.listen(200)

    while True:
        clientSocket, address = server.accept()  # <socket> object, int
        print(f"Connection from {address} has been established!")

        byte_remote = bytearray(remote[0], encoding='utf-8')
        s_remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_remote.connect(remote)
        s_remote.sendall(b"GET / HTTP/1.1\r\nHost: %s\r\n"
                         b"Accept: text/html\r\nConnection: close\r\nuser-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         b"Chrome/88.0.4324.104\r\n\r\n" % byte_remote)

        # enumerate response
        received_data = b''
        while 1:
            data = s_remote.recv(4096)
            received_data = b"%s%s" % (received_data, data)
            if not data:
                break

        print(received_data.decode())

        # 向client发送信息
        PACKET_SIZE = 1024
        clientSocket.send(received_data + b"\x00" * max(PACKET_SIZE - len(received_data), 0))
        # clientSocket.close()


def accept_connections2():
    """在chrome访问<localhost:8888>,
    发送<remote>

    同样功能, 更好的形式
    下一步: rewrite headers
    """
    print("waiting connections...")
    server_config = ("localhost", 8888)
    remote = ("www.example.org", 80)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(server_config)
    server.listen(200)

    while True:
        clientSocket, address = server.accept()  # <socket> object, int
        print(f"Connection from {address} has been established!")

        # 接收remote
        remote_obj = Remote()
        data = remote_obj.get_data(remote)
        print(data.cache_decode())

        # 向client发送信息
        PACKET_SIZE = 4096
        clientSocket.send(data + b"\x00" * max(PACKET_SIZE - len(data), 0))
        # clientSocket.close()

def accept_conn_oop():
    """变成OOP形式
    """
    server_config = ("localhost", 8888)
    p = Proxy(server_config)
    p.start()




def try_cache():

    request = b"GET /~ylzhang/ HTTP/1.1\r\nHost: cs.toronto.edu\r\n" \
                  b"Accept: text/html\r\nConnection: close\r\nuser-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                  b"Chrome/88.0.4324.104 Safari/537.36\r\n\r\n"

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("www.cs.toronto.edu", 80))
    s.send(request)
    data = enumerate_recv(s)

    site = 'www.cs.toronto.edu/~ylzhang/'

    cache(site, data)

    print(data.cache_decode())



def try_read_cahce():
    site = 'www.cs.toronto.edu/~ylzhang/'
    cache = open(encode(site), 'rb')
    bytes = cache.read()
    cache.close()

    print("C")




if __name__ == '__main__':
    try_read_cahce()
