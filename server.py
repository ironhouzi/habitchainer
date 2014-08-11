import socketserver
import json

PORT = 13373
BUFSIZE = 1024


class MyTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


class MyTCPServerHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            recv = self.request.recv(BUFSIZE).decode('UTF-8').strip()
            data = json.loads(recv)
            print(data)
            self.request.sendall(bytes(json.dumps({'return': 'ok'}), 'UTF-8'))
        except Exception as e:
            print('Exception: %s' % (e))

server = MyTCPServer(('', PORT), MyTCPServerHandler)
server.serve_forever()
