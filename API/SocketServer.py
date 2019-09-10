import sys
import socket

from .SuccessfulOAuth import success_html


class SocketServer:
    def __init__(self, host, port):
        self.host = host if host != "" else "127.0.0.1"
        self.port = port

        self.data = {
            "parameters": None,
            "url": None,
            "header": None
        }

    def listen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.bind((self.host, self.port))
        except socket.error as msg:
            print("couldn't bind to %s:%s" % (self.host, self.port))
            sys.exit()

        s.listen(10)

        conn, addr = s.accept()

        success = success_html()

        data = conn.recv(1024)

        conn.send(b"HTTP/1.0 200 OK\n" +
                  b"Content-Type: text/html\n\n" +
                  success.encode("ascii"))

        return data
