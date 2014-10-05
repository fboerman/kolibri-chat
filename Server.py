__author__ = 'williewonka'
__version__ = 1.2

import socketserver
import argparse
import time
import threading
import sys
import hashlib
import uuid
import base64
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from os.path import splitext, basename
import mimetypes
import re
import socket
# import ssl
import PyLogging
from math import floor
from cryptography.fernet import Fernet

users = []
connections = []
connectedclients= []
bannedips = []
MAXCHARS = 124
MASTERPASS = None
Log = None

class ThreadedServerHandler(socketserver.BaseRequestHandler):

    def remove_html_tags(self, data):
        p = re.compile(r'<.*?>')
        return p.sub('', data)


    def CreateFernet(self, passw):
        if len(passw) >= 32:
            return Fernet(base64.urlsafe_b64encode(str.encode(passw[:32])))
        reuse = floor(32/len(passw))
        temp = ""
        for i in range(0, reuse):
            temp += passw
        rest = 32 - len(temp)
        for i in range(0,rest):
            temp += "z"
        return Fernet(base64.urlsafe_b64encode(str.encode(temp)))

    def handle(self): #the handler for the server, this handles the receiving and distributing of messages
        self.websocket = False
        data = self.request.recv(1024)
        addr = self.request.getpeername()[0]
        if "Connection: Upgrade" in str(data, "utf-8"):
            try:
                self.HandShake(str(data, "utf-8"))
                self.websocket = True
            except:
                Print("Incorrect Websocket Upgrade Request from " + addr)
                return
        if self.websocket:
            data = self.parse_frame()
        logindata = ""
        try:
            logindata = json.loads(str(data, "utf-8"))
        except:
            self.SendClient("ERROR: wrong format login package")
            Print("ERROR: client from "+str(addr)+" sent wrong loginrequest")
            Print(logindata)
            return
        NAME = logindata["username"]
        PASS = logindata["password"]
        VERSION = logindata["version"]

        if VERSION != str(__version__):
            self.SendClient("ERROR: wrong version match, server version: "+str(__version__))
            Print("ERROR: client from "+str(addr)+" with username "+NAME+" connected with wrong version "+VERSION)
            return

        found = False

        for u in users:
            if u[0] == NAME:
                if check_password(u[1],PASS):
                    if u[3] == 1:
                        self.SendClient("ERROR: this user is banned")
                        Print("ERROR: client from "+str(addr)+" tried loggin in with banned user "+NAME)
                        return
                    found = True

        if addr in bannedips:
            Print("ERROR: client from banned ip "+addr+" tried logging in with user "+NAME)
            self.SendClient("ERROR: your ip has been banned from this server")
            return

        self.PERSONALFERNET = self.CreateFernet(PASS)

        if found:
            global connections

            for room in connections:
                for connecteduser in room:
                    if connecteduser[0] == NAME:
                        self.SendClient("ERROR: user already logged in")
                        Print("ERROR: client from "+str(addr)+" tried logging in with already online user "+NAME)
                        return

            self.SendClient("OK "+str(len(connections)-1))

            while True:
                try:
                    if self.websocket:
                        ROOM = int(self.parse_frame())
                    else:
                        ROOM = int(self.PERSONALFERNET.decrypt(self.request.recv(1024)))
                except:
                    Print("ERROR: client from "+str(addr)+" with user "+NAME+" disconnected during login process")
                    return

                if ROOM >= len(connections):
                    self.SendClient("ERROR")
                else:
                    self.SendClient("OK")
                    break


            Print("INFO: client "+NAME+" authenticated from "+addr+" into room "+str(ROOM))
            SendRound(NAME + " connected", ROOM, "SERVER")
            user = [NAME, self]
            connections[ROOM].append(user)
            connectedclients.append([NAME, addr])

            while True:
                try:
                    # data = ""
                    try:
                        if self.websocket:
                            data = self.parse_frame()
                            self.data = str(data, "utf-8")
                        else:
                            data = self.request.recv(1024)
                            self.data = str(self.PERSONALFERNET.decrypt(data), "utf-8")
                    except:
                        print(str(data, "utf-8"))


                    if user not in connections[ROOM]:
                        self.SendClient("ERROR: user kicked from this room")
                        return
                    #Print("DEBUG: user "+NAME+" send message:"+self.data)
                    if " " in self.data:
                        try:
                            if self.data.split(" ")[0] == "switch":

                                if int(self.data.split(" ")[1]) >= len(connections):
                                    self.SendClient("OK-ERROR")
                                    continue
                                else:
                                    oldroom = ROOM
                                    connections[ROOM].remove(user)
                                    ROOM = int(self.data.split(" ")[1])
                                    connections[ROOM].append(user)
                                    self.SendClient("OK-switched to room "+str(ROOM))
                                    Print("INFO: user "+NAME+" switched to room "+str(ROOM))
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
                                            Print("INFO: user "+NAME+" changed their password")
                                            self.SendClient("OK-password changed")
                                        else:
                                            self.SendClient("OK-wrong current password")
                                continue
                            elif self.data.split(" ")[0] == "kick":
                                if IsAdmin(NAME) == 0:
                                    Print("INFO: nonadmin user "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                    self.SendClient("OK-you do not have enought rights to do that")
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
                                            Print("INFO: admin "+NAME+" tried kickin fellow admin "+target)
                                            self.SendClient("OK-cant kick fellow admins")
                                            continue
                                    try:
                                        connections[targetroom].remove(targettuple)
                                        for client in connectedclients:
                                            if client[0] == target:
                                                connectedclients.remove(client)
                                        Print("INFO: user "+target+" kicked by admin "+NAME+" from room "+str(targetroom))
                                        SendRound("user "+target+" kicked by admin "+NAME, ROOM, NAME)
                                        self.SendClient("OK-user "+target+" kicked from room")
                                        continue
                                    except:
                                        Print("INFO: admin "+NAME+" tried to kick nonconnected user "+target+" in room "+str(ROOM))
                                        self.SendClient("OK-target user not in this room or not enough adminrights")
                                        continue
                            elif self.data.split(" ")[0] == "ipban":
                                if IsAdmin(NAME) == 2:
                                    target = self.data.split(" ")[1]
                                    found = False
                                    for client in connectedclients:
                                        if client[0] == target:
                                            bannedips.append(client[1])
                                            Print("INFO: admin "+NAME+" banned ip "+client[1]+" from server")
                                            self.SendClient("OK-ip "+client[1]+" banned from server")
                                            found = True
                                    if not found:
                                        self.SendClient("OK-user "+target+"not found")
                                    continue
                                else:
                                    Print("INFO: nonadmin user "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                    self.SendClient("OK-you do not have enough rights to do that")
                                    continue
                            elif self.data.split(" ")[0] == "ipunban":
                                if IsAdmin(NAME) == 2:
                                    try:
                                        bannedips.remove(self.data.split(" ")[1])
                                        Print("INFO: admin "+NAME+" unbanned ip "+self.data.split(" ")[1])
                                        self.SendClient("OK-ip unbanned")
                                    except:
                                        self.SendClient("OK-ip not banned")
                                    continue
                                else:
                                    Print("INFO: admin level 1 "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                    self.SendClient("OK-you do not have enough rights to do that")
                                    continue
                            elif self.data.split(" ")[0] == "ban":
                                if IsAdmin(NAME) == 2:
                                    target = self.data.split(" ")[1]
                                    found = False
                                    for u in users:
                                        if u[0] == target:
                                            u[3] = 1
                                            Print("INFO: admin "+NAME+" banned user "+target)
                                            self.SendClient("OK-user "+target+" banned from server")
                                            for i in range(0, len(connections)):
                                                SendRound("admin "+NAME+" banned user "+target, i, "SERVER")
                                            found = True

                                    if not found:
                                        self.SendClient("OK-user "+target+" not found in database")
                                    continue
                                else:
                                    Print("INFO: admin level 1 "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                    self.SendClient("OK-you do not have enough rights to do that")
                                    continue
                            elif self.data.split(" ")[0] == "unban":
                                if IsAdmin(NAME) == 2:
                                    target = self.data.split(" ")[1]
                                    found = False
                                    for u in users:
                                        if u[0] == target:
                                            u[3] = 0
                                            Print("INFO: admin "+NAME+" unbanned user "+target)
                                            self.SendClient("OK-user "+target+" unbanned from server")
                                            for i in range(0, len(connections)):
                                                SendRound("admin "+NAME+" unbanned user "+target, i, "SERVER")
                                            found = True
                                    if not found:
                                        self.SendClient("OK-user "+target+" not found in database")
                                    continue
                                else:
                                    Print("INFO: admin level 1 "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                    self.SendClient("OK-you do not have enough rights to do that")
                                    continue

                            elif self.data.split(" ")[0] == "whisper":
                                target = self.data.split(":")[0].split(" ")[1]
                                for room in connections:
                                    for u in room:
                                        if u[0] == target:
                                            try:
                                                if u[2]:
                                                    u[1].request.sendall(self.create_frame("whisper "+NAME+": "+self.data.split(":")[1]))
                                                self.SendClient("OK")
                                                Print("whisper from "+NAME+" to "+target+": "+ self.data.split(":")[1])
                                            except:
                                                self.SendClient("OK-target disconnected")
                                            finally:
                                                break

                                continue
                            elif self.data.split(" ")[0] == "adduser":
                                if IsAdmin(NAME) == 2:
                                    user = self.data.split(" ")[1]
                                    password = self.data.split(" ")[2]
                                    if FindUser(user):
                                        self.SendClient("user "+user+" already exists")
                                        continue
                                    else:
                                        users.append([user, hash_password(password), 0, 0])
                                        Print("INFO: user "+user+" added by admin "+NAME)
                                        self.SendClient("OK-new user "+user+" added")
                                        continue
                                else:
                                    self.SendClient("OK-you do not have enough rights to do that")
                                    Print("INFO: user "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                    continue
                            elif self.data.split(" ")[0] == "changepass":
                                if IsAdmin(NAME) == 2:
                                    target = self.data.split(" ")[1]
                                    newpass = hash_password(self.data.split(" ")[2])
                                    found = False
                                    for u in users:
                                        if u[0] == target:
                                            u[1] = newpass
                                            Print("INFO: admin "+NAME+" changed password of user "+target)
                                            self.SendClient("OK-password of user "+target+" changed")
                                            found = True
                                    if not found:
                                        self.SendClient("OK-user "+target+" not found")
                                    continue
                                else:
                                    self.SendClient("OK-you do not have enough rights to do that")
                                    Print("INFO: user "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                    continue
                            elif self.data.split(" ")[0] == "admin":
                                if IsAdmin(NAME) == 2:
                                    user = self.data.split(" ")[1]
                                    level = int(self.data.split(" ")[2])
                                    if not FindUser(user):
                                        self.SendClient("OK-user "+user+" not found")
                                        continue
                                    for u in users:
                                        if u[0] == user:
                                            u[2] = level
                                    Print("INFO: adminlevel for user "+user+" set to "+str(level)+" by admin "+NAME)
                                    self.SendClient("OK-adminlevel for user "+user+" set to "+str(level))
                                    continue
                                else:
                                    self.SendClient("OK-you do not have enough rights to do that")
                                    Print("INFO: user "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                                    continue
                        except:
                            self.SendClient("OK-Error in command")

                    elif self.data == "list":
                        #if IsAdmin(NAME) > 0:
                        list = ""
                        for i in range(0, len(connections)):
                            list += str(i)+";"
                            for u in connections[i]:
                                list += u[0]+";"
                            list += "|"
                        #else:
                        #    list = "connected users in room "+str(ROOM)
                        #    for u in connections[ROOM]:
                        #        list += "\n\t"+u[0]

                        self.SendClient("OK-"+list)
                        continue
                    elif self.data == "testresponse":
                        self.SendClient("OK-TEST COMPLETE")
                        Print("client "+NAME+" requested test response")
                        continue
                    elif self.data == "amiadmin":
                        self.SendClient(str(IsAdmin(NAME)))
                        continue
                    elif self.data == "banlist":
                        if IsAdmin(NAME) == 2:
                            message = ""
                            for u in users:
                                if u[3] == 1:
                                    message += u[0] + "\n"
                            self.SendClient("OK-"+message)
                        else:
                            self.SendClient("OK-you do not have enough rights to do that")
                            Print("INFO: user "+NAME+" tried admin command '"+self.data+"' in room "+str(ROOM))
                        continue
                    global MAXCHARS
                    if len(self.remove_html_tags(self.data)) > MAXCHARS:
                        self.SendClient("OK-Your message has to many characters")
                        Print("client " + NAME + "tried sending a too long message in room " + str(ROOM))
                    else:
                        self.SendClient("OK")
                        if self.data == "":
                            continue
                        SendRound(self.data, ROOM, NAME)
                        Print(NAME + "<"+str(ROOM)+">: " + self.remove_html_tags(self.data))

                except NameError:
                    Print("INFO: client "+NAME+" from "+addr+" in room "+str(ROOM)+" disconnected")
                    try:
                        connections[ROOM].remove(user)
                        connectedclients.remove([NAME, addr])
                    except:
                        pass
                    SendRound("client "+NAME+" disconnected", ROOM, "SERVER")
                    return
        else:
            self.SendClient("ERROR: no known user and password combination")
            Print("ERROR: client from "+str(addr)+" failed login with user "+NAME)
            return




    def HandShake(self, request):
        specificationGUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        websocketkey = ""
        protocol = ""
        for line in request.split("\r\n"):
            if "Sec-WebSocket-Key:" in line:
                websocketkey = line.split(" ")[1]
            elif "Sec-WebSocket-Protocol" in line:
                protocol = line.split(":")[1].strip().split(",")[0].strip()
            elif "Origin" in line:
                self.origin = line.split(":")[0]

        # Print("websocketkey: " + websocketkey + "\n")
        fullKey = hashlib.sha1(websocketkey.encode("utf-8") + specificationGUID.encode("utf-8")).digest()
        acceptKey = base64.b64encode(fullKey)
        # Print("acceptKey: " + str(acceptKey, "utf-8") + "\n")
        if protocol != "":
            handshake = "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Protocol: " + protocol + "\r\nSec-WebSocket-Accept: " + str(acceptKey, "utf-8") + "\r\n\r\n"
        else:
            handshake = "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + str(acceptKey, "utf-8") + "\r\n\r\n"
        # Print(handshake.strip("\n"))
        self.request.send(bytes(handshake, "utf-8"))

    def SendClient(self, message):
        if self.websocket:
            self.request.sendall(self.create_frame(message))
        else:
            message_en = self.PERSONALFERNET.encrypt(str.encode(message))
            # print(message_en)
            self.request.sendall(message_en)

    def create_frame(self, data):
        # pack bytes for sending to client
        frame_head = bytearray(2)

        # set final fragment
        frame_head[0] = self.set_bit(frame_head[0], 7)

        # set opcode 1 = text
        frame_head[0] = self.set_bit(frame_head[0], 0)

        # payload length
        assert len(data) < 126, "haven't implemented that yet"
        frame_head[1] = len(data)

        # add data
        frame = frame_head + data.encode('utf-8')
        # Print("frame crafted for message " + data + ":")
        # Print(list(hex(b) for b in frame))
        return frame

    def is_bit_set(self, int_type, offset):
        mask = 1 << offset
        return not 0 == (int_type & mask)

    def set_bit(self, int_type, offset):
        return int_type | (1 << offset)

    def bytes_to_int(self, data):
        # note big-endian is the standard network byte order
        return int.from_bytes(data, byteorder='big')

    def parse_frame(self):
        """receive data from client"""
        s = self.request
        # read the first two bytes
        frame_head = s.recv(2)

        # very first bit indicates if this is the final fragment
        # Print("final fragment: ", self.is_bit_set(frame_head[0], 7))

        # bits 4-7 are the opcode (0x01 -> text)
        # Print("opcode: ", frame_head[0] & 0x0f)

        # mask bit, from client will ALWAYS be 1
        assert self.is_bit_set(frame_head[1], 7)

        # length of payload
        # 7 bits, or 7 bits + 16 bits, or 7 bits + 64 bits
        payload_length = frame_head[1] & 0x7F
        if payload_length == 126:
            raw = s.recv(2)
            payload_length = self.bytes_to_int(raw)
        elif payload_length == 127:
            raw = s.recv(8)
            payload_length = self.bytes_to_int(raw)
        # Print('Payload is {} bytes'.format(payload_length))

        #masking key
        #All frames sent from the client to the server are masked by a
        #32-bit nounce value that is contained within the frame

        masking_key = s.recv(4)
        # Print("mask: ", masking_key, self.bytes_to_int(masking_key))

        # finally get the payload data:
        masked_data_in = s.recv(payload_length)
        data = bytearray(payload_length)

        # The ith byte is the XOR of byte i of the data with
        # masking_key[i % 4]
        for i, b in enumerate(masked_data_in):
            data[i] = b ^ masking_key[i%4]
        return data


# class TCPServerSSL(socketserver.TCPServer):
#
#     def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
#         socketserver.BaseServer.__init__(self, server_address, RequestHandlerClass)
#         s = socket.socket(self.address_family, self.socket_type)
#
#         self.socket = ssl.wrap_socket(s, server_side=True, certfile="server.crt", keyfile="server.key")
#
#         if bind_and_activate:
#             self.server_bind()
#             self.server_activate()

# class ThreadedSSLTCPServer(socketserver.ThreadingMixIn, TCPServerSSL):
#     pass

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def IsAdmin(User):
    for u in users:
        if u[0] == User:
            return u[2]
    return 0

def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def SendRound(Message, Room, Owner):
    if Message == "":
        return
    for u in connections[Room]:
        if u[0] != Owner:
            Class = u[1]
            try:
                package = ""
                if Owner == "SERVER":
                    package = Owner + " " + Message
                else:
                    package = Owner + ": " + remove_html_tags(Message)
                Class.SendClient(package)
                # if Class.websocket:
                #     Class.request.sendall(Class.create_frame(package))
                # else:
                #     Class.request.sendall(bytes(package, "utf-8"))
            except:
                Print("ERROR: failed to send message to user "+u[0])

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
        Print("read "+str(count)+" users from file to database")
        count = 0
        database = open("bannedips.txt", "r")
        for line in database:
            count += 1
            bannedips.append(line)
        database.close()
        Print("read "+str(count)+" banned ips from file to database")
    except:
        Print("ERROR: failed reading database, server will now exit")
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

class httpRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        allowedtypes = [".html", ".css", ".js", ".json", ".svg", ".eot", ".ttf", ".woff"]
        origin = self.request.getpeername()[0]
        # rootdir = "D:/PycharmProjects/Kolibri_Chat/http"
        filetype =  splitext(basename(self.path))[1]
        rootdir = "http"
        if filetype not in allowedtypes and filetype != "":
            self.send_response(403)
            # Print("Client from " + origin + " asked for forbidden file " + self.path)
            return

        filepath = ""
        if self.path == "/":
            filepath = rootdir + "/kolibri.html"
            filetype = ".html"
        else:
            filepath = rootdir + self.path

        try:
            stream = open(filepath, 'rb')
        except IOError:
            # Print("GET request to nonexisting file " + self.path + " from client " + origin)
            self.send_response(404)
            return

        self.send_response(200)
        try:
            mime = mimetypes.types_map[filetype]
        except:
            mime = 'application/octet-stream'
        self.send_header('content-type', mime)
        self.end_headers()
        self.wfile.write(stream.read())
        stream.close()
        # Print("GET request to file " + self.path + " answered to client " + origin)
        return


    def do_POST(self):
        self.send_response(403)
        return

    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format%args))



def start_httpserver(HOST):
        Print("starting httpserver at port 80 ...")
        mimetypes.init()
        server_address = (HOST, 80)
        global httpserver_thread, httpserver
        httpserver = HTTPServer(server_address, httpRequestHandler)
        httpserver_thread = threading.Thread(target=httpserver.serve_forever)
        httpserver_thread.daemon = True
        httpserver_thread.start()
        Print("http server is running, waiting for connections ...")

def AdminBackDoorServer(connection):
    s = socket.socket()
    s.bind(connection)
    s.listen(5)
    serverid = uuid.uuid4().hex
    Print("admin server started at port " + str(connection[1]))
    while True:
        con, addr = s.accept()
        login = con.recv(1024)
        try:
            logindata = json.loads(login)
            if logindata['user'] == 'admin' and logindata['password'] == MASTERPASS and float(logindata['version']) >= __version__:
                Print("admin connected from " + addr)
                info = {
                    'id' : serverid,
                    'version' : __version__
                }
                try:
                    con.send(json.dumps(info))
                    while True:
                        command = con.recv(1024)
                        if command is 'users':
                            con.send(json.dumps(users))
                        elif command is 'rooms':
                            con.send(json.dumps(connections))
                        elif command is 'clients':
                            con.send(json.dumps(connectedclients))
                        elif command is 'bannedips':
                            con.send(json.dumps(bannedips))
                except:
                    pass
            s.shutdown()
            s.close()
        except:
            pass
        Print("admin disconnected from " + addr)
        s.shutdown()
        s.close()

def Print(message):
    Log.Log(message)
    print(message)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='the server component of kolibri chat')
    parser.add_argument('--ip', nargs='?', const=1, type=str, default="localhost", help='specify the ip adress wich the server will bind to, defaults to localhost')
    parser.add_argument('--port', nargs='?', const=1, type=int, default=600, help='specify the port number, defaults to 9999')
    parser.add_argument('--numrooms', nargs='?', const=1, type=int, default=1, help='number of chatrooms that is available, defaults to 1')
    parser.add_argument('--httpserver', dest='httpserver', action='store_true', help='activates the http server to serve the html client, uses the same host and port 80, default is off')
    # parser.add_argument('--ssl', dest='ssl', action='store_true', help='activates ssl encryption for all socket connections')
    parser.add_argument('--masterpass', nargs='?', const=1, type=str, default='adminpassword', help='master password used to identify at the adminbackdoor')
    parser.add_argument('--adminbackdoor', dest='backdoor', action='store_true', help='activates the administrator backdoor login')
    parser.add_argument('--backdoorport', nargs='?', const=1, type=int, default=500, help='port on which the adminbackdoor will run')
    parser.add_argument('--log', nargs='?', const=1, type=str, default='log.txt', help='specifies path to logfile')
    parser.set_defaults(backdoor = False)
    parser.set_defaults(httpserver = False)
    parser.set_defaults(ssl = False)

    HOST, PORT, NUMROOMS, httpserver, BACKDOOR, MASTERPASS, ADMINPORT, LOGFILE = parser.parse_args().ip, parser.parse_args().port, parser.parse_args().numrooms,\
                                                                             parser.parse_args().httpserver, parser.parse_args().backdoor,\
                                                                             parser.parse_args().backdoor, parser.parse_args().backdoorport, parser.parse_args().log
    # SSL = parser.parse_args().ssl

    for i in range(0, NUMROOMS):
        connections.append([])

    print("logging to " + LOGFILE)
    Log = PyLogging.PyLogging(logname=LOGFILE)

    Print("Kolibri server version "+str(__version__))
    Print("host: " + HOST + ":" + str(PORT))
    Print("reading database ...")
    time.sleep(1)
    ReadDatabase()
    Print("starting server ...")
    time.sleep(1)
    server = None
    # if SSL:
    #     server = ThreadedSSLTCPServer((HOST, PORT), ThreadedServerHandler)
    # else:
    server = ThreadedTCPServer((HOST, PORT), ThreadedServerHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    Print("Server loop running, waiting for connections ...")
    if httpserver:
        start_httpserver(HOST)
    if BACKDOOR:
        Print("starting admin backdoor ...")
        adminserver_thread = threading.Thread(target=AdminBackDoorServer, args=((HOST, ADMINPORT),))
        adminserver_thread.start()
    Print("Typ 'help' for available commands")
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
                    Print("room "+str(i)+": ")
                    for user in connections[i]:
                        Print("\t"+user[0])
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
                            Print("INFO: user "+target+" kicked from room "+str(i))
                            SendRound("user "+target+" kicked by SERVER", i, "SERVER")
                            found = True
                if not found:
                    Print("user "+target+" not connected to server")
            elif command.split(" ")[0] == "ban":
                target = command.split(" ")[1]
                for u in users:
                    if u[0] == target:
                        u[3] = 1
                        Print("INFO: user "+target+" banned")
                        for i in range(0, len(connections)):
                            SendRound("user "+target+" banned by SERVER", i, "SERVER")
            elif command.split(" ")[0] == "unban":
                target = command.split(" ")[1]
                for u in users:
                    if u[0] == target:
                        u[3] = 0
                        Print("INFO user "+target+" unbanned")
                        for i in range(0, len(connections)):
                            SendRound("user "+target+" unbanned by SERVER", i, "SERVER")
            elif command == "userlist":
                Print("users in database:\n\tname\t\tadminlevel\tbanstatus")
                for user in users:
                    Print("\t"+user[0]+"\t\t"+str(user[2])+"\t\t\t"+str(user[3]))
            elif command == "ipbanlist":
                Print("banned ips:")
                for ip in bannedips:
                    Print("\t"+ip)
            elif command.split(" ")[0] == "ipunban":
                bannedips.remove(command.split(" ")[1])
                Print("INFO: ip "+command.split(" ")[1]+" unbanned")
            elif command.split(" ")[0] == "ipban":
                target = command.split(" ")[1]
                for client in connectedclients:
                    if client[0] == target:
                        bannedips.append(client[1])
                        Print("INFO: ip "+client[1]+" banned")
            elif command.split(" ")[0] == "adduser":
                user = command.split(" ")[1]
                password = command.split(" ")[2]
                if FindUser(user):
                    Print("user "+user+" already exists")
                    continue
                else:
                    users.append([user, hash_password(password), 0, 0])
                    Print("INFO: user "+user+" added")
                    continue
            elif command.split(" ")[0] == "admin":
                user = command.split(" ")[1]
                level = int(command.split(" ")[2])
                if not FindUser(user):
                    Print("user "+user+" not found")
                    continue
                for u in users:
                    if u[0] == user:
                        u[2] = level
                Print("INFO: adminlevel for user "+user+" set to "+str(level))
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
                Print("database succesfully written to file")
            elif command.split(" ")[0] == "changepass":
                target = command.split(" ")[1]
                newpass = hash_password(command.split(" ")[2])
                found = False
                for u in users:
                    if u[0] == target:
                        u[1] = newpass
                        Print("password changed!")
                        found = True
                if not found:
                    Print("user not found")
            elif command == "startHttpServer":
                start_httpserver(HOST)
            elif command == "stopHttpServer":
                # global httpserver
                httpserver.shutdown()
                Print("stopped httpserver")
            elif command == "help":
                Print("available commands:\n"
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
                      "\tstartHttpServer: starts the http server for the html5 client\n"
                      "\tstopHttpServer: stops the http server for the html5 client\n"
                      "\thelp : this help message")
        except:
            pass