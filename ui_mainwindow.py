from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setGeometry(QtCore.QRect(10, 10, 780, 400))
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)  # Column count will be set dynamically
        self.tableWidget.setRowCount(0)

        self.pushButton_add = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_add.setGeometry(QtCore.QRect(10, 420, 93, 28))
        self.pushButton_add.setObjectName("pushButton_add")

        self.pushButton_delete = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_delete.setGeometry(QtCore.QRect(110, 420, 93, 28))
        self.pushButton_delete.setObjectName("pushButton_delete")

        self.pushButton_update = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_update.setGeometry(QtCore.QRect(210, 420, 93, 28))
        self.pushButton_update.setObjectName("pushButton_update")

        self.pushButton_query = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_query.setGeometry(QtCore.QRect(310, 420, 93, 28))
        self.pushButton_query.setObjectName("pushButton_query")

        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Database Manager"))
        self.pushButton_add.setText(_translate("MainWindow", "Add"))
        self.pushButton_delete.setText(_translate("MainWindow", "Delete"))
        self.pushButton_update.setText(_translate("MainWindow", "Update"))
        self.pushButton_query.setText(_translate("MainWindow", "Query"))