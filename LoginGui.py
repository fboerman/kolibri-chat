# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'login.ui'
#
# Created: Mon Nov 11 18:53:08 2013
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_LoginWindow(object):
    def setupUi(self, LoginWindow):
        LoginWindow.setObjectName("LoginWindow")
        LoginWindow.resize(401, 199)
        LoginWindow.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedKingdom))
        self.centralwidget = QtGui.QWidget(LoginWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.formLayoutWidget = QtGui.QWidget(self.centralwidget)
        self.formLayoutWidget.setGeometry(QtCore.QRect(30, 40, 331, 91))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtGui.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.lbl_username = QtGui.QLabel(self.formLayoutWidget)
        self.lbl_username.setObjectName("lbl_username")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.lbl_username)
        self.txt_username = QtGui.QLineEdit(self.formLayoutWidget)
        self.txt_username.setObjectName("txt_username")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.txt_username)
        self.lbl_password = QtGui.QLabel(self.formLayoutWidget)
        self.lbl_password.setObjectName("lbl_password")
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.lbl_password)
        self.txt_password = QtGui.QLineEdit(self.formLayoutWidget)
        self.txt_password.setEchoMode(QtGui.QLineEdit.Password)
        self.txt_password.setObjectName("txt_password")
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.txt_password)
        self.lbl_serverip_port = QtGui.QLabel(self.formLayoutWidget)
        self.lbl_serverip_port.setObjectName("lbl_serverip_port")
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.lbl_serverip_port)
        self.txt_serverip_port = QtGui.QLineEdit(self.formLayoutWidget)
        self.txt_serverip_port.setObjectName("txt_serverip_port")
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.txt_serverip_port)
        self.bt_login = QtGui.QPushButton(self.centralwidget)
        self.bt_login.setGeometry(QtCore.QRect(301, 140, 80, 23))
        self.bt_login.setObjectName("bt_login")
        self.lbl_name = QtGui.QLabel(self.centralwidget)
        self.lbl_name.setGeometry(QtCore.QRect(30, 20, 91, 16))
        self.lbl_name.setObjectName("lbl_name")
        self.bt_close = QtGui.QPushButton(self.centralwidget)
        self.bt_close.setGeometry(QtCore.QRect(220, 140, 75, 23))
        self.bt_close.setObjectName("bt_close")
        LoginWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtGui.QStatusBar(LoginWindow)
        self.statusbar.setObjectName("statusbar")
        LoginWindow.setStatusBar(self.statusbar)

        self.retranslateUi(LoginWindow)
        QtCore.QMetaObject.connectSlotsByName(LoginWindow)

    def retranslateUi(self, LoginWindow):
        LoginWindow.setWindowTitle(QtGui.QApplication.translate("LoginWindow", "KolibriLogin", None, QtGui.QApplication.UnicodeUTF8))
        self.lbl_username.setText(QtGui.QApplication.translate("LoginWindow", "Username:", None, QtGui.QApplication.UnicodeUTF8))
        self.txt_username.setPlaceholderText(QtGui.QApplication.translate("LoginWindow", "Username", None, QtGui.QApplication.UnicodeUTF8))
        self.lbl_password.setText(QtGui.QApplication.translate("LoginWindow", "Password:", None, QtGui.QApplication.UnicodeUTF8))
        self.txt_password.setPlaceholderText(QtGui.QApplication.translate("LoginWindow", "Password", None, QtGui.QApplication.UnicodeUTF8))
        self.lbl_serverip_port.setText(QtGui.QApplication.translate("LoginWindow", "Server:", None, QtGui.QApplication.UnicodeUTF8))
        self.txt_serverip_port.setPlaceholderText(QtGui.QApplication.translate("LoginWindow", "Ip:Port", None, QtGui.QApplication.UnicodeUTF8))
        self.bt_login.setText(QtGui.QApplication.translate("LoginWindow", "Login", None, QtGui.QApplication.UnicodeUTF8))
        self.lbl_name.setText(QtGui.QApplication.translate("LoginWindow", "Kolibri Chat Login", None, QtGui.QApplication.UnicodeUTF8))
        self.bt_close.setText(QtGui.QApplication.translate("LoginWindow", "Exit", None, QtGui.QApplication.UnicodeUTF8))

