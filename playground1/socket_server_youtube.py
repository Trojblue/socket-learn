import socket

# 创建TCP Socket
# AFINET: ipv4;  SOCKSTREAM: tcp
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# re-use socket
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((socket.gethostname(), 8888))

# 前最大接收200个unaccepted connections (等待queue)
server.listen(200)


while True:
    clientSocket, address = server.accept() # <socket> object, int
    print(f"Connection from {address} has been established!")

    # 向client发送信息
    clientSocket.send(bytes("welcome to the server!", "utf-8"))

    clientSocket.close()

