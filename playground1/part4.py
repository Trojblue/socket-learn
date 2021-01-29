import select
import socket
import time
import os.path

delay = 0.1
expire_time = 120  # seconds

percent_dict = {
    '!': '%21',
    '/': '%23',
    ':': '%3A',
    '*': '%2A',
    '?': '%3F'
}


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


def to_byte(s: str):
    """return byte form of a string
    """
    return bytearray(s, encoding='utf-8')


def cache_encode(url):
    """url -> percent encoding
    """
    safe_str = ""
    for char in url:
        from_dict = percent_dict.get(char, "")
        if not from_dict:
            safe_str += char
        else:
            safe_str += from_dict

    return safe_str


def cache_decode(url: str):
    """percent encoding -> normal url
    """
    decoded = url
    inv_map = {v: k for k, v in percent_dict.items()}
    for i in inv_map.keys():
        decoded = decoded.replace(i, inv_map[i])

    return decoded


class Cache:
    """general class for cache manipulations
    """

    def __init__(self, url):
        self.url = url
        self.filename = cache_encode(url)
        self.data = None
        self.ctime = None

        self.get_data_if_exists()

    def get_data_if_exists(self):
        """read cache from disk, if exists
        """
        if os.path.exists(self.filename):

            # check expiry
            mtime = os.path.getmtime(self.filename)
            curr_time = time.time()
            time_diff = curr_time - mtime

            if time_diff > expire_time:
                return

            # cache ok, read
            print("fetching data from cache")
            self.data = self.cache_read()
            self.ctime = mtime

    def cache_read(self):
        try:
            cache = open(self.filename, 'rb')
            cache_bytes = cache.read()
            cache.close()
            if cache_bytes == b'':
                return None
            return cache_bytes
        except Exception as e:
            print('read cache error', e)
            return

    def cache_write(self, data):
        """输入data, 输出percent encoded data到硬盘
        url: string
        data: binary data
        """
        f = open(cache_encode(self.url), "wb")
        f.write(data)
        f.close()

    def is_available(self):
        """if cache not found or is expired, self.data will be None
        if not available, will create a new cache
        """
        return bool(self.data)


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
        todo: 应该修改header, 而不是创建新的header
        """
        try:
            self.sock.connect((header.host, header.port))
            send_header = b"GET %s HTTP/1.1\r\nHost: %s\r\n" \
                          b"Accept: text/html\r\nConnection: close\r\nuser-agent: Mozilla/5.0 (Windows NT 10.0;" \
                          b" Win64; x64) Chrome/88.0.4324.104\r\n\r\n" % (to_byte(header.rel), to_byte(header.host))
            self.sock.sendall(send_header)
            return enumerate_recv(self.sock)

        except Exception as e:
            print(e)
            return None

    def close(self):
        self.sock.close()


class Header:
    """用于解析client header
    """

    def __init__(self, sock):
        self.sock = sock
        self.header = enumerate_header(self.sock)
        self.port, self.host, self.rel, self.url = None, None, None, None

        if self.is_empty():
            return
        self.header_list = self.header.split(b'\r\n')
        self.method = self.header[:self.header.index(b' ')]

        self.get_remote()

    def get_remote(self):
        """get remote host info from header
        """
        host_line = self.header_list[0].decode('utf8')  # 'GET /www.cs.toronto.edu/~ylzhang/ HTTP/1.1'
        url = host_line.split(' ')[1][1:]  # `www.cs.toronto.edu/~ylzhang/`

        if ':' in url:
            remote, port = url.split(':')
        else:
            port = 80

        slash_index = url.find('/')

        if slash_index == -1:  # no slash; accessing domain root
            remote_host = url
            remote_rel = '/'
        else:
            remote_host = url[:slash_index]  # `www.cs.utoronto.edu`
            remote_rel = url[slash_index:]  # `/~ylzhang/`

        self.port = port
        self.host = remote_host
        self.rel = remote_rel
        self.url = url

    def is_empty(self):
        return len(self.header) == 0


class Proxy:
    """main program
    """

    def __init__(self, server_config):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind(server_config)
        self.sock.listen(200)

        # select lists
        self.ins = [self.sock]
        self.outs = []
        self.excepts = []
        self.msg_queue = {}

    def run(self):
        print("starting...")
        while self.ins:
            readable, writable, exceptional = select.select(self.ins, self.outs, self.ins)
            for s in readable:
                if s is self.sock:
                    self.accept_s()  # not client, waiting for client
                else:
                    self.parse_fetch_s(s)  # is client, parse request

            for s in writable:  # client ready to receive; send back request
                self.mod_write_s(s)

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

    def mod_write_s(self, s):
        """已经接收到remote, 发送回client
        """
        if s.fileno() == -1:  # closed sock
            print("write error: sock closed")
            return

        if not self.msg_queue[s]:
            self.outs.remove(s)
        else:
            data, ctime = self.msg_queue[s].pop(0)
            if not data:
                return

            # modifying data
            data = self.mod_s(data, ctime)

            print('writing...', data[:50])
            packet_size = 4096
            s.send(data + b"\x00" * max(packet_size - len(data), 0))

    def mod_s(self, data, ctime):
        """modifying outgoing html page
        ctime: timestamp for cache
        """
        body_index = data.find(b'<body>')

        if (body_index == -1):
            pass

        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ctime))
        text = b"cache created at:\n %s" %(to_byte(time_str))
        before_body = data[:body_index+9]
        after_body = data[body_index+9:]
        html_template = b"<p style=\"z-index:9999; position:fixed; top:20px; left:20px; width:200px; " \
                        b"height:100px; background-color:yellow; padding:10px; font-weight:bold;\">%s</p>"%(text)

        new_data = b"%s%s%s" % (before_body, html_template, after_body)

        return new_data

    def parse_fetch_s(self, s):
        """parsing incoming client's header
        解析header, 请求资源, 然后给msg_queue添加一个返回的data对象
        """
        client_socket = s
        client_header = Header(client_socket)

        if client_header.is_empty():
            self.purge_s(s)
            return

        # Cache
        url = client_header.url
        curr_cache = Cache(url)

        if curr_cache.is_available():
            data = curr_cache.data

        else:
            # 从client拿到目标地址, 然后用remote得到data
            remote_obj = Remote()
            data = remote_obj.get_data(client_header)

            if not data:
                self.purge_s(s)
                return
            try:
                print(data.decode())
            except UnicodeError as u:
                print("unable to decode data", u)

            # 写入cache
            curr_cache.cache_write(data)

        # 准备发回数据
        self.msg_queue[s].append((data, curr_cache.ctime))
        if s not in self.outs:
            self.outs.append(s)
        return

    def accept_s(self):
        """accepting new connections
        """
        client_socket, address = self.sock.accept()
        print(f"Connection from {address} has been established!")
        self.sock.setblocking(False)
        self.ins.append(client_socket)
        self.msg_queue[client_socket] = []


if __name__ == '__main__':
    server_config = ("localhost", 8888)
    p = Proxy(server_config)
    p.run()
