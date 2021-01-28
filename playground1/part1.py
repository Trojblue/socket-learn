import socket

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

def to_byte(s:str):
    """return byte form of a string
    """
    return bytearray(s, encoding='utf-8')


class Remote:
    """用class的目的是使用完以后不要被close掉, 否则会connection reset
    """
    def __init__(self):
        """把socket存成self的目的也是保持状态, 防止被close掉
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def get_data(self, header):
        """
        send GET & collect response data from remote
        header: <Header> object
        return: binary response from remote
        """
        try:
            self.sock.connect((header.host, header.port))
            send_header = b"GET %s HTTP/1.1\r\nHost: %s\r\n"\
                             b"Accept: text/html\r\nConnection: close\r\nuser-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "\
                             b"Chrome/88.0.4324.104 Safari/537.36\r\n\r\n" % (to_byte(header.rel), to_byte(header.host))
            self.sock.sendall(send_header)
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

        self.get_remote()

    def get_remote(self):
        """get remote host info from header
        """
        host_line = self.header_list[0].decode('utf8') # 'GET /www.cs.toronto.edu/~ylzhang/ HTTP/1.1'
        url = host_line.split(' ')[1][1:] # `www.cs.toronto.edu/~ylzhang/`

        if ':' in url:
            remote, port = url.split(':')
        else:
            port = 80

        slash_index = url.find('/')

        if slash_index == -1:   # no slash; accessing domain root
            remote_host = url
            remote_rel = '/'
        else:
            remote_host = url[:slash_index] # `www.cs.utoronto.edu`
            remote_rel = url[slash_index:]  # `/~ylzhang/`

        self.port = port
        self.host = remote_host
        self.rel = remote_rel



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
            data = remote_obj.get_data(clientHeader)
            try:
                print(data.decode())
            except UnicodeError as u:
                print("unable to decode data", u)

            # 向client发送信息
            PACKET_SIZE = 4096
            clientSocket.send(data + b"\x00" * max(PACKET_SIZE - len(data), 0))


if __name__ == '__main__':
    server_config = ("localhost", 8888)
    p = Proxy(server_config)
    p.start()


