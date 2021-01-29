import sys, os, time, socket, select

percent_dict = {
    '!': '%21',
    '/': '%23',
    ':': '%3A',
    '*': '%2A',
    '?': '%3F'
}


def enumerate_recv(sock: socket):
    """enumerate response blocks
    :param sock: remote socket
    :return: binary data string
    """
    received_data = b''
    while 1:
        data = sock.recv(4096)
        received_data = b"%s%s" % (received_data, data)
        if not data:
            break
    return received_data


def enumerate_header(sock: socket):
    """enumerate client header
    :param sock: client socket
    :return: binary data string (of client request header)
    """
    received_data = b''
    while 1:
        try:
            data = sock.recv(4096)
        except Exception as e:
            print("[Error] error receiving data", e)
            break
        received_data = b"%s%s" % (received_data, data)
        if received_data.endswith(b'\r\n\r\n') or (not data):
            break
    return received_data


def to_byte(s: str):
    """return byte form of a string
    """
    return bytearray(s, encoding='utf-8')


def cache_encode(url: str):
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


def cache_decode(filename: str):
    """percent encoding -> url
    """
    decoded = filename
    inv_map = {v: k for k, v in percent_dict.items()}
    for i in inv_map.keys():
        decoded = decoded.replace(i, inv_map[i])

    return decoded


class Cache:
    """general class for cache manipulations
    """

    def __init__(self, url: str, expire_time: int):
        """url: target cache url
        filename: filename on local disk
        data: binary data of cache; None if not exist
        mtime: modification time of the cache
        expire_time: cache expire time (s)
        """
        self.url = url
        self.filename = cache_encode(url)
        self.data = None
        self.mtime = None
        self.expire_time = expire_time

        self.get_data_if_exists()

    def get_data_if_exists(self):
        """read cache from disk, if exists
        """
        if os.path.exists(self.filename):

            # check expiry
            mtime = os.path.getmtime(self.filename)
            curr_time = time.time()
            time_diff = curr_time - mtime

            if time_diff > self.expire_time:
                return

            # cache ok, read
            print("[Info] fetching data from cache")
            self.data = self.cache_read()
            self.mtime = mtime

    def cache_read(self):
        """read cache from disk, assuming it exists
        """
        try:
            cache = open(self.filename, 'rb')
            cache_bytes = cache.read()
            cache.close()
            if cache_bytes == b'':
                return None
            return cache_bytes
        except Exception as e:
            print('[Error] read cache error', e)
            return

    def cache_write(self, data):
        """write binary data to local disk
        data: binary response data from remote
        """
        try:
            f = open(cache_encode(self.url), "wb")
            f.write(data)
            f.close()
        except Exception as e:
            print('[Error] write cache error', e)
            return

    def is_available(self):
        """if cache not found or is expired, self.data will be None
        if not available, will create a new cache
        """
        return bool(self.data)


class Remote:
    """general class for communicating with remote web server
    """

    def __init__(self):
        """init remote socket
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

            modded_header = self.mod_header(header)

            # change modded_header to send_header for better reliability
            self.sock.sendall(modded_header)

            received = enumerate_recv(self.sock)
            return received

        except Exception as e:
            print(e)
            return None

    def mod_header(self, header):
        """modify client header to request remote resource
        header: <Header> object
        return: modified header
        """
        modified_header = b"GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\nAccept-Encoding: identity\r\n" \
                          % (to_byte(header.rel), to_byte(header.host))

        skip_list = ("GET", "host:", "Host:", "Connection:", "connection:", "Accept-Encoding:", "accept-encoding:")

        for head in header.header_list:
            if any(words in head.decode('utf-8') for words in skip_list):
                continue
            modified_header = b"%s%s\r\n" % (modified_header, head)

        return modified_header


class Header:
    """general class for client header related operations
    """

    def __init__(self, sock):
        """read request header from client, and save in self

        self.sock: client sock
        self.header: raw header
        port & host & url: client requested port & host & url
        rel: relative path of requested url (`/~ylzhang/`)
        """
        self.sock = sock
        self.header = enumerate_header(self.sock)
        self.port, self.host, self.rel, self.url = None, None, None, None

        if self.is_empty:
            return
        self.header_list = self.header.split(b'\r\n')
        self.method = self.header[:self.header.index(b' ')]

        self.get_remote()

    def get_remote(self):
        """get remote host info from received client header
        """
        host_line = self.header_list[0].decode('utf8')  # 'GET /www.cs.toronto.edu/~ylzhang/ HTTP/1.1'
        url = host_line.split(' ')[1][1:]
        port =  url.split(':') if (':' in url) else 80

        slash_index = url.find('/')

        if slash_index == -1:  # no slash; accessing domain root
            remote_host = url
            remote_rel = '/'
        else:
            remote_host = url[:slash_index]
            remote_rel = url[slash_index:]

        self.port = port  # 80
        self.host = remote_host  # `www.cs.utoronto.edu`
        self.rel = remote_rel  # `/~ylzhang/`
        self.url = url  # `www.cs.toronto.edu/~ylzhang/`

    @property
    def is_empty(self):
        """return True if received empty client header
        """
        return len(self.header) == 0


class Proxy:
    """main proxy program
    usage: proxy.run()
    """

    def __init__(self, server_config, cache_time: int):
        """server_config: Tuple(host, port)
        self.sock: socket object
        cache_time: cache refresh time in seconds
        """
        self.cache_time = cache_time
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.bind(server_config)
        self.sock.listen(200)

        # select lists
        self.ins = [self.sock]
        self.outs = []
        self.excepts = []
        self.msg_queue = {}

    def run(self):
        """starting the proxy
        """
        print("[Info] proxy running...")
        while self.ins:
            readable, writable, exceptions = select.select(self.ins, self.outs, self.ins)
            for s in readable:
                if s is self.sock:
                    self.accept_s()  # not client, waiting for client
                else:
                    self.parse_fetch_s(s)  # is client, parse request

            for s in writable:  # client ready to receive; send back request
                self.mod_write_s(s)

            for s in exceptions:
                print("[Error] exception happened while running")
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
        """received data from remote or cache;
        sending back to client
        s: client socket
        """
        if s.fileno() == -1:  # closed sock
            print("[Error] write error: sock closed")
            return

        if not self.msg_queue[s]:
            self.outs.remove(s)
        else:
            data, ctime = self.msg_queue[s].pop(0)
            if not data:
                return

            # modifying data
            data_mod = self.mod_s(data, ctime)

            print('[Info] writing...', data[:50])
            packet_size = 4096
            s.send(data_mod + b"\x00" * max(packet_size - len(data_mod), 0))

    def mod_s(self, data, ctime):
        """modifying outgoing html page
        ctime: timestamp for cache
        data: binary data to be sent to client
        """
        body_index = data.find(b'<body>')

        if body_index == -1:
            pass

        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ctime))
        text = b"cache created at:\n %s" % (to_byte(time_str))
        before_body = data[:body_index + 7]
        after_body = data[body_index + 7:]
        html_template = b"<p style=\"z-index:9999; position:fixed; top:20px; left:20px; width:200px; " \
                        b"height:100px; background-color:yellow; padding:10px; font-weight:bold;\">%s</p>" % text

        new_data = b"%s%s%s" % (before_body, html_template, after_body)
        template_len = len(html_template)
        new_data = self.mod_file_size(new_data, template_len)

        return new_data

    def mod_file_size(self, data, added_size):
        """modify request size += <added_size>
        data: binary data
        added_size: int
        """
        upper_index = data.find(b"Content-Length:")
        lower_index = data.find(b"content-length:")

        if upper_index == -1 and lower_index == -1:
            # manually add a content-length
            return

        # finding content-length in header, and modify it

        start = upper_index if lower_index == -1 else upper_index
        break_index = data[start:].find(b"\r\n")  # first \r\n after <content-length:>
        end = break_index + start

        new_size = int(data[start:end].decode("utf-8").split(':')[1]) + added_size
        new_content_binary = b"Content-Length: %s" % (to_byte(str(new_size)))

        new_data = b"%s%s%s" % (data[:start], new_content_binary, data[end:])
        return new_data

    def parse_fetch_s(self, s):
        """parsing client's request header,
        then fetch data from remote server
        s: client socket
        """
        client_socket = s
        client_header = Header(client_socket)

        if client_header.is_empty:
            self.purge_s(s)
            return

        # Cache
        url = client_header.url
        curr_cache = Cache(url, self.cache_time)

        if curr_cache.is_available():
            data = curr_cache.data

        else:
            # cache not available; get data from remote
            remote_obj = Remote()
            data = remote_obj.get_data(client_header)

            if not data:
                self.purge_s(s)
                return

            # write to cache
            print("[Info] received %d bytes of data from remote" % len(data))
            curr_cache.cache_write(data)

        # prepare data for write back
        self.msg_queue[s].append((data, curr_cache.mtime))
        if s not in self.outs:
            self.outs.append(s)
        return

    def accept_s(self):
        """accepting new connections
        """
        client_socket, address = self.sock.accept()
        print(f"[Info] {address} connected")
        self.sock.setblocking(False)
        self.ins.append(client_socket)
        self.msg_queue[client_socket] = []


if __name__ == '__main__':
    try:
        cache_timeout = int(sys.argv[1])
    except Exception as e:
        print("[Error] read args error, use default value:", e)
        cache_timeout = 120

    server_config = ("localhost", 8888)
    p = Proxy(server_config, cache_timeout)

    try:
        p.run()
    except KeyboardInterrupt:
        print("[Info] Stopping server")
        sys.exit(1)
