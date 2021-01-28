import select
import socket
import time

delay = 0.1

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
        try:
            data = sock.recv(4096)
        except Exception as e:
            print("error receiving data", e)
            break
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
    用于得到remote的回应
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


class Header:
    """用于解析client header
    """
    def __init__(self, sock):
        self.sock = sock
        self.header = enumerate_header(self.sock)
        if self.is_empty():
            return
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

    def is_empty(self):
        return len(self.header) == 0



class Proxy:
    """main program
    """
    def __init__(self, server_config):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(0)
        self.sock.bind(server_config)
        self.sock.listen(200)

        # select lists
        self.ins = [self.sock]
        self.outs = []
        self.excepts = []
        self.msg_queue = {}

    def run(self):
        """remove indentation
        """
        self.start_select2()


    def start_select2(self):
        print("starting...")
        while self.ins:
            readable, writable, exceptional = select.select(self.ins, self.outs, self.ins)
            for s in readable:
                if s is self.sock:
                    self.accept_s() # not client, waiting for client
                else:
                    self.parse_s(s) # is client, parse request

            for s in writable:  # client ready to receive; send back request
                print("writting....")
                self.write_s(s)

            for s in exceptional:
                print("exception happened")
                self.purge_s(s)

    def purge_s(self, s):
        """remove s from selections, when exception happens or
        when a task is done
        """
        if s in self.outs:
            self.outs.remove(s)
        self.ins.remove(s)
        s.close()
        del self.msg_queue[s]

    def write_s(self, s):
        """已经接收到remote, 发送回client
        """
        if s.fileno() == -1: # closed sock
            print("write error: sock closed")
            return

        if self.msg_queue[s] == []:
            self.outs.remove(s)
        else:
            print('next_msg')
            data = self.msg_queue[s].pop(0)
            PACKET_SIZE = 4096
            s.send(data + b"\x00" * max(PACKET_SIZE - len(data), 0))

    def parse_s(self, s):
        """parsing incoming client's header
        解析header, 请求资源, 然后给msg_queue添加一个返回的data对象
        """
        clientSocket = s
        clientHeader = Header(clientSocket)

        if clientHeader.is_empty():
            self.purge_s(s)
            return

        # 从client拿到目标地址, 然后用remote得到data
        remote_obj = Remote()
        data = remote_obj.get_data(clientHeader)

        if not data:
            self.purge_s(s)
            return

        try:
            print(data.decode())
        except UnicodeError as u:
            print("unable to decode data", u)

        self.msg_queue[s].append(data)
        if s not in self.outs:
            self.outs.append(s)


    def accept_s(self):
        """accepting new connections
        """
        clientSocket, address = self.sock.accept()
        print(f"Connection from {address} has been established!")
        self.sock.setblocking(0)
        self.ins.append(clientSocket)
        self.msg_queue[clientSocket] = []



    def start(self):
        print("waiting connections...")

        server = self.server

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
    p.run()


