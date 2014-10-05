__author__ = 'Williewonka'
__version__ = 1.2

import socket
import time
import sys
import queue
from PySide.QtGui import *
from PySide import QtCore
import LoginGui
import ChatGui
import json
# import ssl
from math import floor
import base64
from cryptography.fernet import Fernet

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock = ssl.wrap_socket(s, ca_certs="server.crt", cert_reqs=ssl.CERT_REQUIRED)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
MAXROOM = 0
NAME = ""
succes = False
dropdown = []
ROOM = 0
verficationpipe = queue.Queue()
whisper = ""


# class Signals(QtCore.QObject):
#     UpdateMenu = QtCore.Signal()
#     UpdatingMenu = False
#
# signals = Signals()

class LoginWindow(QMainWindow, LoginGui.Ui_LoginWindow):

    def __init__(self, parent=None):
        super(LoginWindow, self).__init__(parent)
        self.setupUi(self)

        # noinspection PyTypeChecker
        QApplication.setStyle(QStyleFactory.create("plastique"))

        #debug:
        self.txt_serverip_port.setText("192.168.1.81:600")

        self.bt_close.clicked.connect(self.Close)
        self.bt_login.clicked.connect(self.LoginProcedure)
        self.txt_username.returnPressed.connect(self.LoginProcedure)
        self.txt_password.returnPressed.connect(self.LoginProcedure)
        self.txt_serverip_port.returnPressed.connect(self.LoginProcedure)

    def Close(self):
        self.close()

    def CreateFernet(self, passw):
        global PERSONALFERNET
        if len(passw) >= 32:
            PERSONALFERNET = Fernet(base64.urlsafe_b64encode(str.encode(passw[:32])))
            return
        reuse = floor(32/len(passw))
        temp = ""
        for i in range(0, reuse):
            temp += passw
        rest = 32 - len(temp)
        for i in range(0,rest):
            temp += "z"
        PERSONALFERNET = Fernet(base64.urlsafe_b64encode(str.encode(temp)))


    def LoginProcedure(self):
        global sock
        global MAXROOM
        global ROOM
        global PERSONALFERNET

        if ":" in self.txt_serverip_port.text() and self.txt_username.text() != "" and self.txt_password.text() != "":
            try:
                global NAME
                NAME = self.txt_username.text()
                HOST = self.txt_serverip_port.text().split(":")[0]
                PORT = int(self.txt_serverip_port.text().split(":")[1])
            except:
                QMessageBox.information(self, "Error", "Invalid entry for host and port")
                return
            print('settings: ip: ' + HOST + ' port: ' + str(PORT))
            Echo(self, "setting up connection ...")
            time.sleep(1)
            try:
                sock.connect((HOST, PORT))
            except:
                print("connection failed")
                self.statusbar.showMessage("connection failed")
                QMessageBox.information(self, "Error", "Connection failed, are you sure you put in the right ip and port?")
                sock.close()
                return

            Echo(self, "Connected! Logging in to system ...")
            time.sleep(1)
            logindata = {
                "username": self.txt_username.text(),
                "password": self.txt_password.text(),
                "version": str(__version__)
            }
            loginpackage = json.dumps(logindata)
            try:
                sock.sendall(bytes(loginpackage, "utf-8"))
                #from here on communication is encrypted
                self.CreateFernet(self.txt_password.text())
                answer = str(PERSONALFERNET.decrypt(sock.recv(1024)), "utf-8")
            except:
                print("server disconnected during login communication")
                QMessageBox.information(self, "Error", "server disconnected during login communication")
                sock.close()
                return


            if answer.split(" ")[0] == "OK":
                MAXROOM = int(answer.split(" ")[1])
                Echo(self, "Userlogin succesfull!, Choosing room...")
                while True:
                    #room = input("please select a room(0,"+str(MAXROOM)+"): ")
                    ROOM, ok = QInputDialog.getInteger(self, "Please specify a roomnumber", "Roomnumber:", 0, 0, MAXROOM, 1)
                    if not ok:
                        self.statusbar.showMessage("Aborted")
                        return
                    sock.sendall(PERSONALFERNET.encrypt(str.encode(str(ROOM))))
                    try:
                        answer2 = str(PERSONALFERNET.decrypt(sock.recv(1024)), "utf-8")
                    except:
                        print("server disconnected during login communication, abort")
                        sock.close()
                        QMessageBox.information(self, "Error", "server disconnected during login communication, aborted login sequence")
                    if answer2 != "OK":
                        print("invalid room number, please try again")
                        QMessageBox.informatio(self, "Error", "invalid room number, please try again")
                    else:
                        break

                Echo(self, "Roomlogin succesfull!")

                time.sleep(1)
                global succes
                succes = True
                self.close()
                return
            else:
                Echo(self, "login failed: "+answer.split(":")[1])
                QMessageBox.information(self, "Error", "Login failed!: "+answer.split(":")[1])
                sock.close()
                return

        else:
            QMessageBox.information(self, "Error", "Please check if you have entered all fields correctly")
            return

class ChatWindow(QMainWindow, ChatGui.Ui_MainWindow):
    global sock
    global verficationpipe
    # global signals

    # noinspection PyUnresolvedReferences
    def __init__(self, parent=None):
        global dropdown
        global ROOM
        global MAXROOM
        super(ChatWindow, self).__init__(parent)
        self.setupUi(self)

        # noinspection PyTypeChecker
        QApplication.setStyle(QStyleFactory.create("plastique"))

        Echo(self, "Setting up gui ...")

        try:
            sock.sendall(PERSONALFERNET.encrypt(str.encode("amiadmin")))
            Level = int(PERSONALFERNET.decrypt(sock.recv(1024)))
            sock.sendall(PERSONALFERNET.encrypt(str.encode("list")))
            List = str(PERSONALFERNET.decrypt(sock.recv(1024)), "utf-8")
            sock.sendall(PERSONALFERNET.encrypt(str.encode("banlist")))
            BanList = str(PERSONALFERNET.decrypt(sock.recv(1024)), "utf-8")
        except:
            Echo(self, "Server disconnected")
            QMessageBox.information(self, "Error", "Server disconnected during initializing")
            sock.close()
            return
        # print("DEBUG: Loaded info from server")

        self.UpdateMenu(List, BanList)
        self.cmb_userlists.setCurrentIndex(ROOM)
        self.cmb_userlists.setEnabled(True)
        self.ChangeList()
        # print("DEBUG: updated menu")
        self.bt_send.setEnabled(True)
        self.bt_whisper.setEnabled(True)
        self.bt_logout.setEnabled(True)
        self.txt_message.setReadOnly(False)
        if Level > 0:
            self.bt_kick.setEnabled(True)
        if Level > 1:
            self.bt_ban.setEnabled(True)
            self.bt_ipban.setEnabled(True)
        # print("DEBUG: enabled buttons")
        self.thread = ServerHandler(self)
        self.thread.start()
        # print("DEBUG: thread started")
        self.cmb_userlists.currentIndexChanged.connect(self.ChangeList)
        self.bt_logout.clicked.connect(self.Logout)
        self.bt_send.clicked.connect(self.Send)
        self.txt_message.returnPressed.connect(self.Send)
        self.thread.terminated.connect(self.ServerDrop)
        self.bt_switch.clicked.connect(self.RoomSwitch)
        self.bt_whisper.clicked.connect(self.Whisper)
        self.bt_kick.clicked.connect(self.Kick)
        self.bt_ban.clicked.connect(self.Ban)
        self.bt_ipban.clicked.connect(self.IpBan)
        #signals.UpdateMenu.connect(self.UpdateMenu)
        # print("DEBUG: connected signals")
        self.statusbar.showMessage("Server status: connected")

    def Kick(self):
        if self.cmb_userlists.currentText() is not "Banned Users":
            for user in self.lst_users.selectedItems():
                message = "kick " + user.text()
                self.SendServer(message, "OK")

    def IpBan(self):
        if self.cmb_userlists.currentText() is not "Banned Users":
            for user in self.lst_users.selectedItems():
                message = "ipban " + user.text()
                self.SendServer(message, "OK")

    def Ban(self):
        if self.cmb_userlists.currentText() is not "Banned Users":
            for user in self.lst_users.selectedItems():
                message = "ban " + user.text()
                self.SendServer(message, "OK")
        else:
            for user in self.lst_users.selectedItems():
                message = "unban " + user.text()
                self.SendServer(message, "OK")

    def Whisper(self):
        global whisper

        try:
            whisper = self.lst_users.selectedItems()[0].text()
            # self.bt_whisper.setText("<font color=\"red\">whisper</font>")
            self.bt_whisper.setStyleSheet("color: rgb(255,0,0)")
        except:
            whisper = ""
            self.bt_whisper.setStyleSheet("color: rgb(0,0,0)")
            # self.bt_whisper.setText("whisper")

    def RoomSwitch(self):
        self.SendServer("switch "+str(self.cmb_userlists.currentIndex()), "OK")

    def ServerDrop(self):
        Echo(self, "Server disconnected!")
        self.bt_send.setEnabled(False)
        self.bt_whisper.setEnabled(False)
        self.bt_logout.setEnabled(False)
        self.txt_message.setReadOnly(False)
        self.bt_kick.setEnabled(False)
        self.bt_ban.setEnabled(False)
        self.bt_ipban.setEnabled(False)
        self.cmb_userlists.setEnabled(False)

    def Send(self):
        if whisper is "":
            self.SendServer(self.txt_message.text(), "OK")
        else:
            self.SendServer("whisper " + whisper + ":" + self.txt_message.text(), "OK")

    def SendServer(self, message, token):
        global PERSONALFERNET
        self.txt_message.clear()
        if message.split(" ")[0] not in ["help", "switch", "ban", "unban", "ipban", "changepass", "changeownpass"]:
            self.txt_messages.append(NAME+": "+message)
        try:
            sock.sendall(PERSONALFERNET.encrypt(str.encode(message)))
        except:
            self.ServerDrop()

        verficationpipe.put(token)
        verficationpipe.join()

    def UpdateMenu(self, List, BanList):
        global dropdown
        global sock
        dropdown = []
        self.cmb_userlists.clear()
        for room in List.split("-")[1].split("|"):
            p = room.split(";")
            if p == "":
                continue
            self.cmb_userlists.addItem(p[0])
            del p[0]
            roomlist = []
            for user in p:
                if user != "":
                    roomlist.append(user)
            dropdown.append(roomlist)
        if "OK" not in BanList:
            banlist = []
            for user in BanList.split("\n"):
                banlist.append(user)
            dropdown.append(banlist)
            self.cmb_userlists.addItem("Banned Users")
        elif BanList == "":
            self.cmb_userlists.addItem("Banned Users")

    def ChangeList(self):
        self.lst_users.clear()
        self.lst_users.addItems(dropdown[self.cmb_userlists.currentIndex()])
        if self.cmb_userlists.currentIndex() != ROOM and not self.cmb_userlists.currentIndex() > MAXROOM:
            self.bt_switch.setEnabled(True)
        else:
            self.bt_switch.setEnabled(False)

    def Logout(self):
        self.thread.terminate()
        Echo(self, "Logging off...")
        sock.close()
        self.close()




def Echo(self, message):
    self.statusbar.showMessage(message)
    print(message)

LoginWindow.Echo = Echo
ChatWindow.Echo = Echo

class ServerHandler(QtCore.QThread):
    global verficationpipe
    global dropdown
    global sock
    # global signals

    def __init__(self, form, parent=None):
        super(ServerHandler, self).__init__(parent)
        self.form = form

    def UpdateGUI(self):
        try:
            sock.sendall(bytes("list", "utf-8"))
            List = str(sock.recv(1024), "utf-8")
            sock.sendall(bytes("banlist", "utf-8"))
            BanList = str(sock.recv(1024), "utf-8")
        except:
            sock.close()
            self.terminate()
            return
        form.UpdateMenu(List, BanList)

    def run(self):
        global ROOM
        global PERSONALFERNET
        while True:
            try:
                serverinput = str(PERSONALFERNET.decrypt(sock.recv(1024)), "utf-8")
            except:
                sock.close()
                self.terminate()
                return
            if not verficationpipe.empty():
                token = verficationpipe.get()
                if token not in serverinput:
                    self.form.txt_messages.append("<font color = \"red\">verification with server failed!</font>")
                    verficationpipe.task_done()
                    continue
                else:
                    if "-" in serverinput:
                        self.form.txt_messages.append("<font color=\"blue\">INFO: "+serverinput.split("-")[1]+"</font>")
                        if "switched to room" in serverinput:
                            self.UpdateGUI()
                            try:
                                ROOM = int(serverinput.split(" ")[3])
                            except:
                                self.form.txt_messages.append("<font color = \"red\">invalid serverresponse!</font>")
                            form.cmb_userlists.setCurrentIndex(ROOM)
                    verficationpipe.task_done()
                    continue
            else:
                if serverinput != "":
                    if ("connected" in serverinput or "switched" in serverinput or "disconnected" in serverinput) and ":" not in serverinput:
                        self.form.txt_messages.append("<font color = \"orange\"> " + serverinput + " </font>")
                        self.UpdateGUI()
                        form.cmb_userlists.setCurrentIndex(ROOM)
                    elif "SERVER" in serverinput:
                        self.form.txt_messages.append("<font color = \"olive\"> " + serverinput + " </font>")
                    else:
                        self.form.txt_messages.append(serverinput)
                    continue

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = LoginWindow()
    form.show()
    app.exec_()

    if succes:
        form = ChatWindow()
        form.show()
        app.exec_()

        #print('you can now begin sending messages\ntype help for available commands')
        #while True:
        #    if not thread.is_alive():
        #        sock.close()
        #        sys.exit()
        #
        #    clientinput = input()
        #    if clientinput == "help":
        #        print("available commands:\n"
        #              "\tclose: disconnect from the server\n"
        #              "\tswitch <roomnumber>: switch chatroom\n"
        #              "\tkick <user>: kick user from room\n"
        #              "\tlist: list of connected users\n"
        #              "\twhisper <user>:<message> : send a private message to a connected user, crossroom supported\n"
        #              "\tchangeownpass <oldpass> <newpass> : changes your password\n"
        #              "commands below are for admins only\n"
        #              "\tipban <user>: bans the ip of the given user, you need to issue kick to end current session\n"
        #              "\tipunban <ip>: unbans given ip\n"
        #              "\tban <user>: bans the given user, same provision as ipban\n"
        #              "\tunban <user>: unbans given user\n"
        #              "\tadduser <user> <password> : creates a new user with the specified info\n"
        #              "\tchangepass <user> <newpassword> : changes the password of given user\n"
        #              "\thelp: this helpmessage")
        #    elif clientinput == "close":
        #        print("disconnecting client")
        #        sock.close()
        #        sys.exit()
        #    elif clientinput.split(" ")[0] == "switch":
        #        try:
        #            if int(clientinput.split(" ")[1]) > MAXROOM:
        #                print("ERROR: invalid roomnumber")
        #                continue
        #            else:
        #                SendServer(clientinput, sock, "OK")
        #                print("INFO: Room succesfully switched!")
        #                continue
        #        except:
        #            print("ERROR: wrong syntax")
        #    else:
        #        SendServer(clientinput, sock, "OK")