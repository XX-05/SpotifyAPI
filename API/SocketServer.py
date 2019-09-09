import sys
import socket


class SocketServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.data = {
            "parameters": None,
            "url": None,
            "header": None
        }

    def listen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.bind(self.host, self.port)
        except socket.error as msg:
            print("couldn't bind to %s:%s" % (self.host, self.port))
            sys.exit()

        s.listen(10)

        while 1:
            conn, addr = s.accept()
            print(conn, addr)
