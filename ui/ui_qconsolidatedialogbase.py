# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/qconsolidatedialogbase.ui'
#
# Created: Sat May 17 18:49:35 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_QConsolidateDialog(object):
    def setupUi(self, QConsolidateDialog):
        QConsolidateDialog.setObjectName(_fromUtf8("QConsolidateDialog"))
        QConsolidateDialog.resize(400, 119)
        self.gridLayout = QtGui.QGridLayout(QConsolidateDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(QConsolidateDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.leOutputDir = QtGui.QLineEdit(QConsolidateDialog)
        self.leOutputDir.setObjectName(_fromUtf8("leOutputDir"))
        self.horizontalLayout.addWidget(self.leOutputDir)
        self.btnBrowse = QtGui.QPushButton(QConsolidateDialog)
        self.btnBrowse.setObjectName(_fromUtf8("btnBrowse"))
        self.horizontalLayout.addWidget(self.btnBrowse)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 1, 1, 1)
        self.progressBar = QtGui.QProgressBar(QConsolidateDialog)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridLayout.addWidget(self.progressBar, 1, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(QConsolidateDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 1, 1, 1)

        self.retranslateUi(QConsolidateDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), QConsolidateDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), QConsolidateDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(QConsolidateDialog)

    def retranslateUi(self, QConsolidateDialog):
        QConsolidateDialog.setWindowTitle(_translate("QConsolidateDialog", "QConsolidate", None))
        self.label.setText(_translate("QConsolidateDialog", "Output directory", None))
        self.btnBrowse.setText(_translate("QConsolidateDialog", "Browse...", None))

