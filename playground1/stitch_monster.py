import socket

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



