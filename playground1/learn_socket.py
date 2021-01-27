import signal
import socket
import threading


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
    request = b"GET / HTTP/1.1\nHost: stackoverflow.com\n\n"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("www.cs.toronto.edu/~ylzhang/", 80))
    s.send(request)
    result = s.recv(10000)
    while (len(result) > 0):
        print(result)
        result = s.recv(10000)


def socket_get():
    # !/usr/bin/env python

    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        # s.connect(("www.example.org", 80))
        # s.connect(("www.cs.torornto.edu/~ylzhang", 80))
        # s.sendall(b"GET / HTTP/1.1\r\nHost: cs.torornto.edu\r\nAccept: text/html\r\nConnection: close\r\n\r\n")

        s.connect(("localhost", 5555))
        s.sendall(b"GET / HTTP/1.1\r\nHost: localhost:5555\r\nAccept: text/html\r\nConnection: close\r\n\r\n")

        while True:

            data = s.recv(1024)

            if not data:
                break

            print(data.decode())


if __name__ == '__main__':
    socket_get()

