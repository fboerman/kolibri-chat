__author__ = 'williewonka-2013'
__version__ = 0.9

import socketserver
import argparse
import time
import threading
import sys
import hashlib
import uuid

users = []
connections = []
connectedclients= []
bannedips = []

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

        for u in users:
            if u[0] == NAME:
                if check_password(u[1],PASS):
                    if u[3] == 1:
                        self.request.sendall(bytes("ERROR: this user is banned", "utf-8"))
                        print("ERROR: client from "+str(addr)+" tried loggin in with banned user "+NAME)
                        return
                    found = True

        if addr in bannedips:
            print("ERROR: client from banned ip "+addr+" tried logging in with user "+NAME)
            self.request.sendall(bytes("ERROR: your ip has been banned from this server", "utf-8"))
            return

        if found:
            global connections
            for room in connections:
                for connecteduser in room:
                    if connecteduser[0] == NAME:
                        self.request.sendall(bytes("ERROR: user already logged in", "utf-8"))
                        print("ERROR: client from "+str(addr)+" tried logging in with already online user "+NAME)
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
            connectedclients.append([NAME, addr])

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
                                SendRound("INFO: user "+NAME+" switched to other room", oldroom, "SERVER")
                                SendRound("connected", ROOM, NAME)
                                continue
                        elif self.data.split(" ") == "changeownpass":
                            oldpass = self.data.split(" ")[1]
                            newpass = self.data.split(" ")[2]
                            for u in users:
                                if u[0] == NAME:
                                    if check_password(u[1], oldpass):
                                        u[1] = hash_password(newpass)
                                        print("INFO: user "+NAME+" changed their password")
                                        self.request.sendall(bytes("OK-password changed", "utf-8"))
                                    else:
                                        self.request.sendall(bytes("OK-wrong current password", "utf-8"))
                            continue
                        elif self.data.split(" ")[0] == "kick":
                            if IsAdmin(NAME) == 0:
                                print("INFO: nonadmin user "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                self.request.sendall(bytes("OK-you do not have enought rights to do that", "utf-8"))
                                continue
                            else:
                                targetroom = 0
                                target = self.data.split(" ")[1]
                                targettuple = []
                                if  IsAdmin(NAME) == 1:
                                    targetroom = ROOM
                                    for u in connections[ROOM]:
                                        if u[0] == target:
                                            targettuple = u
                                elif IsAdmin(NAME) == 2:
                                    for i in range(0, len(connections)):
                                        for u in connections[i]:
                                            if u[0] == target:
                                                targettuple = u
                                if IsAdmin(NAME) == 1:
                                    if u[3] > 0:
                                        print("INFO: admin "+NAME+" tried kickin fellow admin "+target)
                                        self.request.sendall(bytes("OK-cant kick fellow admins", "utf-8"))
                                        continue
                                try:
                                    connections[targetroom].remove(targettuple)
                                    for client in connectedclients:
                                        if client[0] == target:
                                            connectedclients.remove(client)
                                    print("INFO: user "+target+" kicked by admin "+NAME+" from room "+str(targetroom))
                                    SendRound("user "+target+" kicked by admin "+NAME, ROOM, NAME)
                                    self.request.sendall(bytes("OK-user "+target+" kicked from room", "utf-8"))
                                    continue
                                except:
                                    print("INFO: admin "+NAME+" tried to kick nonconnected user "+target+" in room "+str(ROOM))
                                    self.request.sendall(bytes("OK-target user not in this room or not enough adminrights", "utf-8"))
                                    continue
                        elif self.data.split(" ")[0] == "ipban":
                            if IsAdmin(NAME) == 2:
                                target = self.data.split(" ")[1]
                                found = False
                                for client in connectedclients:
                                    if client[0] == target:
                                        bannedips.append(client[1])
                                        print("INFO: admin "+NAME+" banned ip "+client[1]+" from server")
                                        self.request.sendall(bytes("OK-ip "+client[1]+" banned from server", "utf-8"))
                                        found = True
                                if not found:
                                    self.request.sendall(bytes("OK-user "+target+"not found", "utf-8"))
                                continue
                            else:
                                print("INFO: nonadmin user "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                self.request.sendall(bytes("OK-you do not have enough rights to do that", "utf-8"))
                                continue
                        elif self.data.split(" ")[0] == "ipunban":
                            if IsAdmin(NAME) == 2:
                                try:
                                    bannedips.remove(self.data.split(" ")[1])
                                    print("INFO: admin "+NAME+" unbanned ip "+self.data.split(" ")[1])
                                    self.request.sendall(bytes("OK-ip unbanned", "utf-8"))
                                except:
                                    self.request.sendall(bytes("OK-ip not banned", "utf-8"))
                                continue
                            else:
                                print("INFO: admin level 1 "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                self.request.sendall(bytes("OK-you do not have enough rights to do that", "utf-8"))
                                continue
                        elif self.data.split(" ")[0] == "ban":
                            if IsAdmin(NAME) == 2:
                                target = self.data.split(" ")[1]
                                found = False
                                for u in users:
                                    if u[0] == target:
                                        u[3] = 1
                                        print("INFO: admin "+NAME+" banned user "+target)
                                        self.request.sendall(bytes("OK-user "+target+" banned from server", "utf-8"))
                                        for i in range(0, len(connections)):
                                            SendRound("admin "+NAME+" banned user "+target, i, "SERVER")
                                        found = True

                                if not found:
                                    self.request.sendall(bytes("OK-user "+target+" not found in database", "utf-8"))
                                continue
                            else:
                                print("INFO: admin level 1 "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                self.request.sendall(bytes("OK-you do not have enough rights to do that", "utf-8"))
                                continue
                        elif self.data.split(" ")[0] == "unban":
                            if IsAdmin(NAME) == 2:
                                target = self.data.split(" ")[1]
                                found = False
                                for u in users:
                                    if u[0] == target:
                                        u[3] = 0
                                        print("INFO: admin "+NAME+" unbanned user "+target)
                                        self.request.sendall(bytes("OK-user "+target+" unbanned from server", "utf-8"))
                                        for i in range(0, len(connections)):
                                            SendRound("admin "+NAME+" unbanned user "+target, i, "SERVER")
                                        found = True
                                if not found:
                                    self.request.sendall(bytes("OK-user "+target+" not found in database", "utf-8"))
                                continue
                            else:
                                print("INFO: admin level 1 "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                self.request.sendall(bytes("OK-you do not have enough rights to do that", "utf-8"))
                                continue

                        elif self.data.split(" ")[0] == "whisper":
                            target = self.data.split(":")[0].split(" ")[1]
                            for room in connections:
                                for u in room:
                                    if u[0] == target:
                                        try:
                                            u[1].request.sendall(bytes("whisper "+NAME+": "+self.data.split(":")[1], "utf-8"))
                                            self.request.sendall(bytes("OK", "utf-8"))
                                            print("whisper from "+NAME+" to "+target+": "+ self.data.split(":")[1])
                                        except:
                                            self.request.sendall(bytes("OK-target disconnected", "utf-8"))
                                        finally:
                                            break

                            continue
                        elif self.data.split(" ")[0] == "adduser":
                            if IsAdmin(NAME) == 2:
                                user = self.data.split(" ")[1]
                                password = self.data.split(" ")[2]
                                if FindUser(user):
                                    self.request.sendall(bytes("user "+user+" already exists", "utf-8"))
                                    continue
                                else:
                                    users.append([user, hash_password(password), 0, 0])
                                    print("INFO: user "+user+" added by admin "+NAME)
                                    self.request.sendall(bytes("OK-new user "+user+" added", "utf-8"))
                                    continue
                            else:
                                self.request.sendall(bytes("OK-you do not have enough rights to do that", "utf-8"))
                                print("INFO: user "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                continue
                        elif self.data.split(" ")[0] == "changepass":
                            if IsAdmin(NAME) == 2:
                                target = self.data.split(" ")[1]
                                newpass = hash_password(self.data.split(" ")[2])
                                found = False
                                for u in users:
                                    if u[0] == target:
                                        u[1] = newpass
                                        print("INFO: admin "+NAME+" changed password of user "+target)
                                        self.request.sendall(bytes("OK-password of user "+target+" changed", "utf-8"))
                                        found = True
                                if not found:
                                    self.request.sendall(bytes("OK-user "+target+" not found", "utf-8"))
                                continue
                            else:
                                self.request.sendall(bytes("OK-you do not have enough rights to do that", "utf-8"))
                                print("INFO: user "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                continue
                        elif self.data.split(" ")[0] == "admin":
                            if IsAdmin(NAME) == 2:
                                user = self.data.split(" ")[1]
                                level = int(self.data.split(" ")[2])
                                if not FindUser(user):
                                    self.request.sendall(bytes("OK-user "+user+" not found", "utf-8"))
                                    continue
                                for u in users:
                                    if u[0] == user:
                                        u[2] = level
                                print("INFO: adminlevel for user "+user+" set to "+str(level)+" by admin "+NAME)
                                self.request.sendall(bytes("OK-adminlevel for user "+user+" set to "+str(level),"utf-8"))
                                continue
                            else:
                                self.request.sendall(bytes("OK-you do not have enough rights to do that", "utf-8"))
                                print("INFO: user "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                continue

                    elif self.data == "list":
                        if IsAdmin(NAME) > 0:
                            list = "connected users in room\n"
                            for i in range(0, len(connections)):
                                list += str(i)+":\n"
                                for u in connections[i]:
                                    list += "\t"+u[0]+"\n"
                        else:
                            list = "connected users in room "+str(ROOM)
                            for u in connections[ROOM]:
                                list += "\n\t"+u[0]

                        self.request.sendall(bytes("OK-"+list, "utf-8"))
                        continue

                    self.request.sendall(bytes("OK","utf-8"))
                    if self.data == "":
                        continue
                    SendRound(self.data, ROOM, NAME)
                    print(NAME + "<"+str(ROOM)+">: " + self.data)

                except:
                    print("INFO: client "+NAME+" from "+addr+" in room "+str(ROOM)+" disconnected")
                    try:
                        connections[ROOM].remove(user)
                        connectedclients.remove([NAME, addr])
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

def IsAdmin(User):
    for u in users:
        if u[0] == User:
            return u[2]
    return 0

def SendRound(Message, Room, Owner):
    if Message == "":
        return
    for u in connections[Room]:
        if u[0] != Owner:
            socket = u[1]
            try:
                socket.request.sendall(bytes(Owner+": "+Message, "utf-8"))
            except:
                print("ERROR: failed to send message to user "+u[0])

def FindUser(user):
    for u in users:
        if u[0] == user:
            return True
    return False

def ReadDatabase():
    try:
        database = open("users.txt", "r")
        count = 0
        for line in database:
            count += 1
            users.append([line.split(" ")[0].strip("\n"), line.split(" ")[1], int(line.split(" ")[2]), int(line.split(" ")[3].strip("\n"))])
        database.close()
        print("read "+str(count)+" users from file to database")
        count = 0
        database = open("bannedips.txt", "r")
        for line in database:
            count += 1
            bannedips.append(line)
        database.close()
        print("read "+str(count)+" banned ips from file to database")
    except:
        print("ERROR: failed reading database, server will now exit")
        time.sleep(1)
        database.close()
        sys.exit()

def hash_password(password):
    # uuid is used to generate a random number
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

def check_password(hashed_password, user_password):
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()

ThreadedServerHandler.SendRound = SendRound
ThreadedServerHandler.IsAdmin = IsAdmin
ThreadedServerHandler.FindUser = FindUser
ThreadedServerHandler.hash_password = hash_password
ThreadedServerHandler.check_password = check_password

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
    ReadDatabase()
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
            elif command == "list":
                for i in range(0, len(connections)):
                    print("room "+str(i)+": ")
                    for user in connections[i]:
                        print("\t"+user[0])
            elif command.split(" ")[0] == "kick":
                target = command.split(" ")[1]
                found = False
                for i in range(0, len(connections)):
                    for user in connections[i]:
                        if user[0] == target:
                            connections[i].remove(user)
                            for client in connectedclients:
                                if client[0] == target:
                                    connectedclients.remove(client)
                            print("INFO: user "+target+" kicked from room "+str(i))
                            SendRound("user "+target+" kicked by SERVER", i, "SERVER")
                            found = True
                if not found:
                    print("user "+target+" not connected to server")
            elif command.split(" ")[0] == "ban":
                target = command.split(" ")[1]
                for u in users:
                    if u[0] == target:
                        u[3] = 1
                        print("INFO: user "+target+" banned")
                        for i in range(0, len(connections)):
                            SendRound("user "+target+" banned by SERVER", i, "SERVER")
            elif command.split(" ")[0] == "unban":
                target = command.split(" ")[1]
                for u in users:
                    if u[0] == target:
                        u[3] = 0
                        print("INFO user "+target+" unbanned")
                        for i in range(0, len(connections)):
                            SendRound("user "+target+" unbanned by SERVER", i, "SERVER")
            elif command == "userlist":
                print("users in database:\n\tname\t\tadminlevel\tbanstatus")
                for user in users:
                    print("\t"+user[0]+"\t\t"+str(user[2])+"\t\t\t"+str(user[3]))
            elif command == "ipbanlist":
                print("banned ips:")
                for ip in bannedips:
                    print("\t"+ip)
            elif command.split(" ")[0] == "ipunban":
                bannedips.remove(command.split(" ")[1])
                print("INFO: ip "+command.split(" ")[1]+" unbanned")
            elif command.split(" ")[0] == "ipban":
                target = command.split(" ")[1]
                for client in connectedclients:
                    if client[0] == target:
                        bannedips.append(client[1])
                        print("INFO: ip "+client[1]+" banned")
            elif command.split(" ")[0] == "adduser":
                user = command.split(" ")[1]
                password = command.split(" ")[2]
                if FindUser(user):
                    print("user "+user+" already exists")
                    continue
                else:
                    users.append([user, hash_password(password), 0, 0])
                    print("INFO: user "+user+" added")
                    continue
            elif command.split(" ")[0] == "admin":
                user = command.split(" ")[1]
                level = int(command.split(" ")[2])
                if not FindUser(user):
                    print("user "+user+" not found")
                    continue
                for u in users:
                    if u[0] == user:
                        u[2] = level
                print("INFO: adminlevel for user "+user+" set to "+str(level))
                continue
            elif command == "reload":
                del users[:]
                ReadDatabase()
            elif command == "savedb":
                newfile = ""
                for u in users:
                    newfile += u[0]+" "+u[1]+" "+str(u[2])+" "+str(u[3])+"\n"
                file = open("users.txt", "w")
                file.write(newfile)
                file.close()
                newfile = ""
                for ip in bannedips:
                    newfile += ip +"\n"
                file = open("bannedips.txt", "w")
                file.write(newfile)
                file.close()
                print("database succesfully written to file")
            elif command.split(" ")[0] == "changepass":
                target = command.split(" ")[1]
                newpass = hash_password(command.split(" ")[2])
                found = False
                for u in users:
                    if u[0] == target:
                        u[1] = newpass
                        print("password changed!")
                        found = True
                if not found:
                    print("user not found")
            elif command == "help":
                print("available commands:\n"
                      "\tsay>room:message : when no room given, broadcast to all the rooms otherwise just send to specified room\n"
                      "\tkick user : kicks user from the server\n"
                      "\tlist : list of connected users per room\n"
                      "\tuserlist : list of users in database\n"
                      "\tipban <user>: bans the ip of the given user, you need to issue kick to end current session\n"
                      "\tipunban <ip>: reverses effect from ipban command\n"
                      "\tban <user>: bans the given user, same provision as ipban\n"
                      "\tunban <user>: reverses effect of ban command\n"
                      "\tipbanlist: gives a list of banned ips\n"
                      "\tadmin <user> <adminlevel> : sets adminlevel of specified user\n"
                      "\tadduser <user> <password> : creates a new user with the specified info\n"
                      "\tchangepass <user> <newpassword> : changes the password of given user\n"
                      "\tsavedb: saves the database to file\n"
                      "\treload: reloads the database files\n"
                      "\thelp : this help message")
        except:
            pass