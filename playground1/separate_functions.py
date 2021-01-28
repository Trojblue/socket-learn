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


class Remote:
    """用class的目的是使用完以后不要被close掉, 否则会connection reset
    """
    def __init__(self):
        """把socket存成self的目的也是保持状态, 防止被close掉
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def get_remote_data(self, remote):
        """返回一个example.org的data
        remote: Tuple(host, port)
        """
        byte_remote = bytearray(remote[0], encoding='utf-8')

        try:
            # send GET
            self.sock.connect(remote)
            self.sock.sendall(b"GET / HTTP/1.1\r\nHost: %s\r\n"
                             b"Accept: text/html\r\nConnection: close\r\nuser-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             b"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36\r\n\r\n" % byte_remote)

            # enumerate response
            received_data = b''
            while 1:
                data = self.sock.recv(4096)
                received_data = b"%s%s" % (received_data, data)
                if not data:
                    break

            return received_data

        except Exception as e:
            print(e)
            return b"EXCEPTION"



    def close(self):
        self.sock.close()