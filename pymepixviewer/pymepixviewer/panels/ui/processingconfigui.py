# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'processingconfig.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(506, 223)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.groupBox_3 = QtWidgets.QGroupBox(Form)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_6 = QtWidgets.QLabel(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_4.addWidget(self.label_6)
        self.min_event_window = QtWidgets.QLineEdit(self.groupBox_3)
        self.min_event_window.setObjectName("min_event_window")
        self.horizontalLayout_4.addWidget(self.min_event_window)
        self.max_event_window = QtWidgets.QLineEdit(self.groupBox_3)
        self.max_event_window.setObjectName("max_event_window")
        self.horizontalLayout_4.addWidget(self.max_event_window)
        self.label_10 = QtWidgets.QLabel(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy)
        self.label_10.setObjectName("label_10")
        self.horizontalLayout_4.addWidget(self.label_10)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.verticalLayout_4.addWidget(self.groupBox_3)
        self.groupBox_4 = QtWidgets.QGroupBox(Form)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_4)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_8 = QtWidgets.QLabel(self.groupBox_4)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_10.addWidget(self.label_8)
        self.tot_threshold = QtWidgets.QSpinBox(self.groupBox_4)
        self.tot_threshold.setMaximum(30000)
        self.tot_threshold.setObjectName("tot_threshold")
        self.horizontalLayout_10.addWidget(self.tot_threshold)
        self.verticalLayout_3.addLayout(self.horizontalLayout_10)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_7 = QtWidgets.QLabel(self.groupBox_4)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_5.addWidget(self.label_7)
        self.centroid_skip = QtWidgets.QSpinBox(self.groupBox_4)
        self.centroid_skip.setMaximum(30000)
        self.centroid_skip.setObjectName("centroid_skip")
        self.horizontalLayout_5.addWidget(self.centroid_skip)
        self.verticalLayout_3.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_9 = QtWidgets.QLabel(self.groupBox_4)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_6.addWidget(self.label_9)
        self.blob_num = QtWidgets.QSpinBox(self.groupBox_4)
        self.blob_num.setMinimum(1)
        self.blob_num.setMaximum(32)
        self.blob_num.setObjectName("blob_num")
        self.horizontalLayout_6.addWidget(self.blob_num)
        self.verticalLayout_3.addLayout(self.horizontalLayout_6)
        self.verticalLayout_4.addWidget(self.groupBox_4)
        self.verticalLayout.addLayout(self.verticalLayout_4)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.groupBox_3.setTitle(_translate("Form", "Pixel Processing"))
        self.label_6.setText(_translate("Form", "Event window:"))
        self.min_event_window.setText(_translate("Form", "0"))
        self.max_event_window.setText(_translate("Form", "10000"))
        self.label_10.setText(_translate("Form", "us"))
        self.groupBox_4.setTitle(_translate("Form", "Centroiding"))
        self.label_8.setText(_translate("Form", "TOT threshold:"))
        self.tot_threshold.setToolTip(_translate("Form", "Determines the TOT threshold"))
        self.label_7.setText(_translate("Form", "Centroid Skip:"))
        self.centroid_skip.setToolTip(_translate("Form", "Allows the blob finder to skip every nth packet (1 means all are processed)"))
        self.label_9.setText(_translate("Form", "No Process:"))
        self.blob_num.setToolTip(_translate("Form", "Allows the blob finder to skip every nth packet (1 means all are processed)"))

