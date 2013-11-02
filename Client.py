__author__ = 'Williewonka-2013'
__version__ = 0.5

import socket
import argparse
import time
import sys
import threading
import queue

verficationpipe = queue.Queue()

def ServerHandler(s,clientname):
    while True:
        try:
            serverinput = str(s.recv(1024), "utf-8")
        except:
            print("server dropped, exiting client")
            s.close()
            sys.exit()

        if not verficationpipe.empty():
            token = verficationpipe.get()
            if serverinput != token:
                print("verification with server failed: "+serverinput+", exiting  client")
                s.close()
                sys.exit()
            else:
                verficationpipe.task_done()
        else:
            if serverinput != "":
                print(serverinput)

def SendServer(message, s, verificationtoken):
    try:
        s.sendall(bytes(message, "utf-8"))
    except:
        if thread.is_alive():
            print("connection with server lost, exiting client")
            s.close()
        sys.exit()

    verficationpipe.put(verificationtoken)
    verficationpipe.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='client to connect to a kolibri chat server')
    parser.add_argument('--ip', nargs='?', const=1, type=str, required=True, help='specify the ip of the server, required')
    parser.add_argument('--port', nargs='?', const=1, type=int, required=True, help='specify the port number, required')
    parser.add_argument('--name', nargs='?', const=1, type=str, required=True, help='specify your login name, required')
    parser.add_argument('--password', nargs='?', const=1, type=str, required=True, help='specify your password, required')
    HOST, PORT, NAME, PASS = parser.parse_args().ip, parser.parse_args().port, parser.parse_args().name, parser.parse_args().password
    print('Welcome to kolibri chat client version '+str(__version__))
    print('settings: ip: ' + HOST + ' port: ' + str(PORT))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('setting up connection ...')
    time.sleep(1)
    try:
        sock.connect((HOST, PORT))
    except:
        print("connection failed, are you sure you have right port and ip?\nclient will now exit")
        sock.close()
        time.sleep(1)
        sys.exit()

    print("connected! logging in to system ...")
    time.sleep(1)
    sock.sendall(bytes(NAME+" "+PASS+" "+str(__version__), "utf-8"))
    try:
        answer = str(sock.recv(1024), "utf-8")
    except:
        print("server disconnected during login communication, exiting client")
        sock.close()
        sys.exit()

    if answer.split(" ")[0] == "OK":
        MAXROOM = int(answer.split(" ")[1])
        print("userlogin succesfull!")
        while True:
            room = input("please select a room(0,"+str(MAXROOM)+"): ")
            sock.sendall(bytes(room, "utf-8"))
            try:
                answer2 = str(sock.recv(1024), "utf-8")
            except:
                print("server disconnected during login communication, exiting client")
                sock.close()
                sys.exit()
            if answer2 != "OK":
                print("invalid room number, please try again")
            else:
                break

        thread = threading.Thread(target=ServerHandler, args=(sock,NAME))
        thread.deamon = True
        thread.start()
        print('roomlogin succesfull\nyou can now begin sending messages\ntype help for available commands')
        while True:
            if not thread.is_alive():
                break

            clientinput = input()
            if clientinput == "help":
                print("available commands:\n\tclose: disconnect from the server\n\tswitch <roomnumber>: switch chatroom\n\thelp: this helpmessage")
            elif clientinput == "close":
                print("disconnecting client")
                sock.close()
                sys.exit()
            elif clientinput.split(" ")[0] == "switch":
                try:
                    if int(clientinput.split(" ")[1]) > MAXROOM:
                        print("ERROR: invalid roomnumber")
                        continue
                    else:
                        SendServer(clientinput, sock, "OK")
                        print("INFO: Room succesfully switched!")
                        continue
                except:
                    print("ERROR: wrong syntax")
            else:
                SendServer(clientinput, sock, "OK")

    else:
        print("login failed: "+answer+", client will now exit")
        sock.close()
        sys.exit()