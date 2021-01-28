class Forward:
    def __init__(self):
        pass

    def start(self):
        print("HEYHEYHEY")
        return 10101


def find_replace():
    client_request = b'GET /www.NOTADOMAIN.com/s/asdasdasd HTTP/1.1\r\nAccept: */*\r\n' \
                     b'Postman-Token: 84c0ca6b-16d8-43c3-9c09-6931773f7f60\r\nHost: localhost:8890\r\n\r\n'

    sample_out = (b"GET / HTTP/1.1\r\nHost: %s\r\n"
                   b"Accept: text/html\r\nConnection: close\r\nuser-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   b"Chrome/88.0.4324.104 Safari/537.36\r\n\r\n" % b'www.example.org')




if __name__ == '__main__':
    num = Forward().start()

    print("D")