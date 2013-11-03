__author__ = 'williewonka-2013'
__version__ = 0.6

import socketserver
import argparse
import time
import threading
import sys

users = []
connections = []

class ThreadedServerHandler(socketserver.BaseRequestHandler):

    def handle(self): #the handler for the server, this handles the receiving and distributing of messages
        addr = self.request.getpeername()[0]
        self.data = self.request.recv(1024)
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
            print("ERROR: client from "+str(addr)+" with username "+NAME+" connected with wrong version "+VERSION)
            return

        found = False
        ADMIN = 0

        for u in users:
            if u[0] == NAME:
                if u[1] == PASS:
                    found = True
                    ADMIN = u[2]


        if found:
            global connections
            for room in connections:
                for connecteduser in room:
                    if connecteduser[0] == NAME:
                        self.request.sendall(bytes("ERROR: user already logged in", "utf-8"))
                        print("ERROR: client from "+str(addr)+" logged in with already online user "+NAME)
                        return

            self.request.sendall(bytes("OK "+str(len(connections)-1),  "utf-8"))

            while True:
                try:
                    ROOM = int(self.request.recv(1024))
                except:
                    print("ERROR: client from "+str(addr)+" with user "+NAME+" disconnected during login process")
                    return

                if ROOM >= len(connections):
                    self.request.sendall(bytes("ERROR", "utf-8"))
                else:
                    self.request.sendall(bytes("OK", "utf-8"))
                    break


            print("INFO: client "+NAME+" authenticated from "+addr+" into room "+str(ROOM))
            SendRound("connected", ROOM, NAME)
            user = [NAME, self]
            connections[ROOM].append(user)

            while True:
                try:
                    self.data = str(self.request.recv(1024), "utf-8")

                    if user not in connections[ROOM]:
                        self.request.sendall(bytes("ERROR: user kicked from this room", "utf-8"))
                        return

                    if " " in self.data:
                        if self.data.split(" ")[0] == "switch":
                            if int(self.data.split(" ")[1]) >= len(connections):
                                self.request.sendall(bytes("ERROR", "utf-8"))
                                continue
                            else:
                                oldroom = ROOM
                                connections[ROOM].remove(user)
                                ROOM = int(self.data.split(" ")[1])
                                connections[ROOM].append(user)
                                self.request.sendall(bytes("OK", "utf-8"))
                                print("INFO: user "+NAME+" switched to room "+str(ROOM))
                                SendRound("user "+NAME+" switched to other room", oldroom, "SERVER")
                                continue
                        elif self.data.split(" ")[0] == "kick":
                            if  ADMIN == 1:
                                target = self.data.split(" ")[1]
                                targettuple = []
                                for u in connections[ROOM]:
                                    if u[0] == target:
                                        targettuple = u

                                try:
                                    connections[ROOM].remove(targettuple)
                                    print("INFO: user "+target+" kicked by admin "+NAME+" from room "+str(ROOM))
                                    self.request.sendall(bytes("OK-user "+target+" kicked from room", "utf-8"))
                                    continue
                                except:
                                    print("INFO: user "+NAME+" tried to kick nonconnected user "+target+" in room "+str(ROOM))
                                    self.request.sendall(bytes("OK-target user not in room", "utf-8"))
                                    continue
                            else:
                                print("INFO: nonadmin user "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                self.request.sendall(bytes("OK-you do not have enought right to do that", "utf-8"))
                                continue

                    self.request.sendall(bytes("OK","utf-8"))

                    SendRound(self.data, ROOM, NAME)
                    #for u in connections[ROOM]:
                    #    if u[0] != NAME:
                    #        socket = u[1]
                    #        socket.request.sendall(bytes(NAME+": "+self.data, "utf-8"))

                    print(NAME + "<"+str(ROOM)+">: " + self.data)

                except:
                    print("INFO: client "+NAME+" from "+addr+" in room "+str(ROOM)+" disconnected")
                    try:
                        connections[ROOM].remove(user)
                    except:
                        pass
                    SendRound("client "+NAME+" disconnected", ROOM, "SERVER")
                    return
        else:
            self.request.sendall(bytes("ERROR: no known user and password combination", "utf-8"))
            print("ERROR: client from "+str(addr)+" failed login with user "+NAME)
            return



class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def SendRound(Message, Room, Owner):
    for u in connections[Room]:
        if u[0] != Owner:
            socket = u[1]
            try:
                socket.request.sendall(bytes(Owner+": "+Message, "utf-8"))
            except:
                print("ERROR: failed to send message to user "+u[0])

ThreadedServerHandler.SendRound = SendRound

if __name__ == "__main__":
    print("Kolibri server version "+str(__version__))
    parser = argparse.ArgumentParser(description='the server component of kolibri chat')
    parser.add_argument('--ip', nargs='?', const=1, type=str, default="localhost", help='specify the ip adress wich the server will bind to, defaults to localhost')
    parser.add_argument('--port', nargs='?', const=1, type=int, default=6000, help='specify the port number, defaults to 9999')
    parser.add_argument('--numrooms', nargs='?', const=1, type=int, default=1, help='number of chatrooms that is available, defaults to 1')

    HOST, PORT, NUMROOMS = parser.parse_args().ip, parser.parse_args().port, parser.parse_args().numrooms

    for i in range(0, NUMROOMS):
        connections.append([])

    print("port: "+str(PORT))
    print("reading database ...")
    time.sleep(1)
    database = open("users.txt", "r")
    count = 0
    for line in database:
        count += 1
        try:
            users.append([line.split(" ")[0].strip("\n"), line.split(" ")[1], int(line.split(" ")[2].strip("\n"))])
        except:
            print("ERROR: failed reading database, server will now exit")
            time.sleep(1)
            database.close()
            sys.exit()

    database.close()

    print("read "+str(count)+" users from database")
    print("starting server ...")
    time.sleep(1)
    server = ThreadedTCPServer((HOST, PORT), ThreadedServerHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running, waiting for connections ...")
    print("Typ 'help' for available commands")
    while True:
        command = input()
        try:
            if "say" in command:
                if ">" in command:
                    room = int(command.split(">")[1].split(":")[0])
                    message = command.split(">")[1].split(":")[1]
                    SendRound(message, room, "SERVER")
                else:
                    message = command.split(":")[1]
                    for i in range (0, len(connections)):
                        SendRound(message, i, "SERVER")
            elif command == "help":
                print("available commands:\n"
                      "\tsay>room:message : when no room given, broadcast to all the rooms otherwise just send to specified room\n"
                      "\tkick user : kicks user from the server\n"
                      "\thelp : this help message")
        except:
            pass