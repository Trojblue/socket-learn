import socket


def get_request(remote:str):
    """输出一个巨复杂的request
    remote: binary string
    """

    curr_request = b"GET / HTTP/1.1\r\nHost: %s\r\n" \
                   b"Accept: text/html\r\nConnection: close\r\n" \
                   b"user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/88.0.4324.104\r\n" \
                   b"\r\n" % remote

    pass

def enumerate_recv(sock):
    received_data = b''
    while 1:
        data = sock.recv(4096)
        received_data = b"%s%s" % (received_data, data)
        if not data:
            break
    return received_data

def enumerate_header(sock):
    received_data = b''
    while 1:
        data = sock.recv(4096)
        received_data = b"%s%s" % (received_data, data)
        if received_data.endswith(b'\r\n\r\n') or (not data):
            break
    return received_data

class Remote:
    """用class的目的是使用完以后不要被close掉, 否则会connection reset
    """
    def __init__(self):
        """把socket存成self的目的也是保持状态, 防止被close掉
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def get_data(self, remote_config):
        """返回一个example.org的data
        remote_config: Tuple(host, port)
        """
        host = bytearray(remote_config[0], encoding='utf-8')

        try:
            # send GET
            self.sock.connect(remote_config)

            send_header = b"GET / HTTP/1.1\r\nHost: %s\r\n"\
                             b"Accept: text/html\r\nConnection: close\r\nuser-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "\
                             b"Chrome/88.0.4324.104 Safari/537.36\r\n\r\n" % host

            self.sock.sendall(send_header)

            # enumerate response
            return enumerate_recv(self.sock)

        except Exception as e:
            print(e)
            return b"EXCEPTION"

    def close(self):
        self.sock.close()


class ClientServer:
    """accepting connection from client (browser)
    """
    def __init__(self, server_config):
        """server_config: Tuple(host, port)
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(server_config)
        self.sock.listen(200)

    def accept(self):
        return self.sock.accept()


class Header:
    def __init__(self, sock):
        self.sock = sock
        self.header = enumerate_header(self.sock)
        self.header_list = self.header.split(b'\r\n')
        self.method = self.header[:self.header.index(b' ')]
        self.remote_conf=None

        self.get_remote()

    def get_remote(self):
        """get remote host info from header
        """
        host_line = self.header_list[0].decode('utf8')
        host = host_line.split(' ')[1][1:] # removing first character (/)

        if ':' in host:
            host, port = host.split(':')
        else:
            port = 80

        self.remote_conf = (host, port)


    # def get_


class Proxy:
    """main program
    """
    def __init__(self, server_config):
        self.server_conf = server_config


    def start(self):
        print("waiting connections...")

        server = ClientServer(self.server_conf)

        while True:
            clientSocket, address = server.accept()  # <socket> object, int
            print(f"Connection from {address} has been established!")
            clientHeader = Header(clientSocket)

            # 从client拿到目标地址, 然后用remote得到data
            remote_obj = Remote()
            data = remote_obj.get_data(clientHeader.remote_conf)
            print(data.decode())

            # 向client发送信息
            PACKET_SIZE = 4096
            clientSocket.send(data + b"\x00" * max(PACKET_SIZE - len(data), 0))



