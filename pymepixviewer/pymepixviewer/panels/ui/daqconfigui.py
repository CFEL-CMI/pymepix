# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pymepixviewer\panels\ui\daqconfig.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(482, 510)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tabWidget = QtWidgets.QTabWidget(Form)
        self.tabWidget.setObjectName("tabWidget")
        self.acqtab = AcquisitionConfig()
        self.acqtab.setObjectName("acqtab")
        self.tabWidget.addTab(self.acqtab, "")
        self.viewtab = ViewerConfig()
        self.viewtab.setObjectName("viewtab")
        self.tabWidget.addTab(self.viewtab, "")
        self.proctab = ProcessingConfig()
        self.proctab.setObjectName("proctab")
        self.tabWidget.addTab(self.proctab, "")
        self.verticalLayout_2.addWidget(self.tabWidget)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(Form)
        self.label.setAlignment(QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.elapsed_time_h = QtWidgets.QLCDNumber(Form)
        self.elapsed_time_h.setLineWidth(1)
        self.elapsed_time_h.setSegmentStyle(QtWidgets.QLCDNumber.Flat)
        self.elapsed_time_h.setObjectName("elapsed_time_h")
        self.horizontalLayout.addWidget(self.elapsed_time_h)
        self.elapsed_time_m = QtWidgets.QLCDNumber(Form)
        self.elapsed_time_m.setSegmentStyle(QtWidgets.QLCDNumber.Flat)
        self.elapsed_time_m.setObjectName("elapsed_time_m")
        self.horizontalLayout.addWidget(self.elapsed_time_m)
        self.elapsed_time_s = QtWidgets.QLCDNumber(Form)
        self.elapsed_time_s.setSegmentStyle(QtWidgets.QLCDNumber.Flat)
        self.elapsed_time_s.setObjectName("elapsed_time_s")
        self.horizontalLayout.addWidget(self.elapsed_time_s)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.start_acq = QtWidgets.QPushButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.start_acq.sizePolicy().hasHeightForWidth())
        self.start_acq.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.start_acq.setFont(font)
        self.start_acq.setObjectName("start_acq")
        self.verticalLayout.addWidget(self.start_acq)
        self.end_acq = QtWidgets.QPushButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.end_acq.sizePolicy().hasHeightForWidth())
        self.end_acq.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.end_acq.setFont(font)
        self.end_acq.setObjectName("end_acq")
        self.verticalLayout.addWidget(self.end_acq)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_12 = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_12.setFont(font)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_3.addWidget(self.label_12)
        self.text_status = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.text_status.setFont(font)
        self.text_status.setObjectName("text_status")
        self.horizontalLayout_3.addWidget(self.text_status)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.retranslateUi(Form)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.acqtab), _translate("Form", "Acquisition"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.viewtab), _translate("Form", "Viewer"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.proctab), _translate("Form", "Processing"))
        self.label.setText(_translate("Form", "Acq Time:"))
        self.start_acq.setText(_translate("Form", "Start Acquisition"))
        self.end_acq.setText(_translate("Form", "Stop Acquisition"))
        self.label_12.setText(_translate("Form", "Status:"))
        self.text_status.setText(_translate("Form", "Live"))


from pymepixviewer.panels.acqconfig import AcquisitionConfig
from pymepixviewer.panels.processingconfig import ProcessingConfig
from pymepixviewer.panels.viewerconfig import ViewerConfig
