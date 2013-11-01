__author__ = 'williewonka-2013'
__version__ = 0.3

import socketserver
import argparse
import time
import threading

connectedusers = []
users = []

class ThreadedServerHandler(socketserver.BaseRequestHandler):

    def handle(self): #the handler for the server, this handles the receiving and distributing of messages
        addr = self.request.getpeername()[0]
        self.data = self.request.recv(1024).strip()
        data = str(self.data, "utf-8")
        try:
            NAME = data.split(" ")[0]
            PASS = data.split(" ")[1]
            VERSION = data.split(" ")[2]
        except:
            self.request.sendall(bytes("ERROR: wrong format login package", "utf-8"))
            print("ERROR: client from "+str(addr)+" sent wrong loginrequest")
            return

        if VERSION != str(__version__):
            self.request.sendall(bytes("ERROR: wrong version match, server version: "+str(__version__), "utf-8"))
            print("ERROR: client from "+str(addr)+"with username "+NAME+" connected with wrong version "+VERSION)
            return

        client = [NAME, PASS]
        global connectedusers

        if client not in users:
            self.request.sendall(bytes("ERROR: no known user and password combination", "utf-8"))
            print("ERROR: client from "+str(addr)+" failed login with user "+NAME)
            return

        for cu in connectedusers:
            if cu[0] == NAME:
                self.request.sendall(bytes("ERROR: user already logged in", "utf-8"))
                print("ERROR: client from "+str(addr)+" logged in with already online user "+NAME)
                return

        self.request.sendall(bytes("OK",  "utf-8"))

        print("INFO: client "+NAME+" authenticated from "+addr)
        user = [NAME, self]
        connectedusers.append(user)
        while 1:
            try:
                self.data = str(self.request.recv(1024), "utf-8")
                self.request.sendall(bytes("OK","utf-8"))

                for u in connectedusers:
                    if u[0] != NAME:
                        socket = u[1]
                        socket.request.sendall(bytes(NAME+": "+self.data, "utf-8"))

                print(NAME + ": " + self.data)

            except:
                print("INFO: client "+NAME+" from "+addr+" disconnected")
                connectedusers.remove(user)
                return




class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    print("Kolibri server version "+str(__version__))
    parser = argparse.ArgumentParser(description='the server component of kolibri chat')
    parser.add_argument('--port', nargs='?', const=1, type=int, default=9999, help='specify the port number, defaults to 9999')
    HOST, PORT = "192.168.0.104", parser.parse_args().port
    print("port: "+str(PORT))
    print("reading database ...")
    time.sleep(1)
    database = open("users.txt", "r")
    count = 0
    for line in database:
        count += 1
        users.append([line.split(" ")[0].strip("\n"), line.split(" ")[1].strip("\n")])
    database.close()

    print("read "+str(count)+" users from database")
    print("starting server ...")
    time.sleep(1)
    server = ThreadedTCPServer((HOST, PORT), ThreadedServerHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running, waiting for connections ...")
    while True:
        pass