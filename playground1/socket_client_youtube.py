import socket





def simpleserver():
    # 创建TCP Socket
    # AFINET: ipv4;  SOCKSTREAM: tcp
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.bind(('localhost', 10290))

    s.connect((socket.gethostname(), 8888))
    # s.connect(("https://gcp.gkd.icu/", 80))

    while True:
        # 太长的消息会分条发送
        # 可以把bufsize调小来看效果
        bufsize = 1024
        msg = s.recv(bufsize)

        print(msg.decode("utf-8"))

if __name__ == '__main__':
    simpleserver()





