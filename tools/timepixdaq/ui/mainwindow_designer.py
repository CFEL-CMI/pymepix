# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1151, 1048)
        self.visualizer = QtWidgets.QWidget(MainWindow)
        self.visualizer.setObjectName("visualizer")
        MainWindow.setCentralWidget(self.visualizer)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1151, 22))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuTimepix = QtWidgets.QMenu(self.menubar)
        self.menuTimepix.setObjectName("menuTimepix")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionConnect = QtWidgets.QAction(MainWindow)
        self.actionConnect.setObjectName("actionConnect")
        self.actionModify_Pixels = QtWidgets.QAction(MainWindow)
        self.actionModify_Pixels.setObjectName("actionModify_Pixels")
        self.actionPreferences = QtWidgets.QAction(MainWindow)
        self.actionPreferences.setObjectName("actionPreferences")
        self.actionImport = QtWidgets.QAction(MainWindow)
        self.actionImport.setObjectName("actionImport")
        self.menuFile.addAction(self.actionImport)
        self.menuTimepix.addAction(self.actionConnect)
        self.menuTimepix.addAction(self.actionModify_Pixels)
        self.menuEdit.addAction(self.actionPreferences)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuTimepix.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "PymepixDAQ"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuTimepix.setTitle(_translate("MainWindow", "Timepix"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.actionConnect.setText(_translate("MainWindow", "Connect"))
        self.actionModify_Pixels.setText(_translate("MainWindow", "Modify Pixels"))
        self.actionPreferences.setText(_translate("MainWindow", "Preferences"))
        self.actionImport.setText(_translate("MainWindow", "Import"))

