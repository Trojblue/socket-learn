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

def get_data(sock):
    received_data = b''
    while 1:
        data = sock.recv(4096)
        received_data = b"%s%s" % (received_data, data)
        if not data:
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
            self.sock.sendall(b"GET / HTTP/1.1\r\nHost: %s\r\n"
                             b"Accept: text/html\r\nConnection: close\r\nuser-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             b"Chrome/88.0.4324.104 Safari/537.36\r\n\r\n" % host)

            # enumerate response
            return get_data(self.sock)

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
        clientSocket, address = self.sock.accept()


        return clientSocket, address


class Proxy:
    """main program
    """
    def __init__(self, server_config, remote_config):
        self.server_conf = server_config
        self.remote_conf = remote_config

    def start(self):
        print("waiting connections...")

        server = ClientServer(self.server_conf)

        while True:
            clientSocket, address = server.accept()  # <socket> object, int
            print(f"Connection from {address} has been established!")

            # 接收remote
            remote_obj = Remote()
            data = remote_obj.get_data(self.remote_conf)
            print(data.decode())

            # 向client发送信息
            PACKET_SIZE = 4096
            clientSocket.send(data + b"\x00" * max(PACKET_SIZE - len(data), 0))



