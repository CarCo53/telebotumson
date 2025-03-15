import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QInputDialog
from ui_mainwindow import Ui_MainWindow
import sqlite3

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.connection = sqlite3.connect("bot_database.db")
        self.table_name = "User_Data"
        self.columns = self.get_columns()
        self.load_data()
        self.pushButton_add.clicked.connect(self.add_record)
        self.pushButton_delete.clicked.connect(self.delete_record)
        self.pushButton_update.clicked.connect(self.update_record)
        self.pushButton_query.clicked.connect(self.query_data)

    def get_columns(self):
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({self.table_name})")
        columns_info = cursor.fetchall()
        columns = [col[1] for col in columns_info]
        return columns

    def load_data(self):
        query = f"SELECT * FROM {self.table_name}"
        result = self.connection.execute(query)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(len(self.columns))
        self.tableWidget.setHorizontalHeaderLabels(self.columns)
        for row_number, row_data in enumerate(result):
            self.tableWidget.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.tableWidget.setItem(row_number, column_number, QTableWidgetItem(str(data)))

    def add_record(self):
        values = []
        for column in self.columns:
            value, ok = QInputDialog.getText(self, f"Add Record", f"Enter {column}:")
            if ok:
                values.append(value)
            else:
                return
        placeholders = ', '.join(['?' for _ in self.columns])
        query = f"INSERT INTO {self.table_name} ({', '.join(self.columns)}) VALUES ({placeholders})"
        self.connection.execute(query, values)
        self.connection.commit()
        self.load_data()

    def delete_record(self):
        selected_row = self.tableWidget.currentRow()
        if selected_row >= 0:
            id_item = self.tableWidget.item(selected_row, 0)
            if id_item:
                query = f"DELETE FROM {self.table_name} WHERE {self.columns[0]} = ?"
                self.connection.execute(query, (id_item.text(),))
                self.connection.commit()
                self.tableWidget.removeRow(selected_row)
        else:
            QMessageBox.warning(self, "Warning", "Please select a row to delete")

    def update_record(self):
        selected_row = self.tableWidget.currentRow()
        if selected_row >= 0:
            id_item = self.tableWidget.item(selected_row, 0)
            values = {}
            for column in self.columns[1:]:
                item = self.tableWidget.item(selected_row, self.columns.index(column))
                new_value, ok = QInputDialog.getText(self, "Update Record", f"Enter new {column}:", text=item.text() if item else "")
                if ok:
                    values[column] = new_value
                else:
                    return
            set_clause = ', '.join([f"{col} = ?" for col in values.keys()])
            query = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.columns[0]} = ?"
            self.connection.execute(query, list(values.values()) + [id_item.text()])
            self.connection.commit()
            self.load_data()
        else:
            QMessageBox.warning(self, "Warning", "Please select a row to update")

    def query_data(self):
        column_name, ok = QInputDialog.getText(self, "Query Data", "Enter column name to query:")
        if ok:
            value, ok = QInputDialog.getText(self, "Query Data", f"Enter value for {column_name}:")
            if ok and column_name in self.columns:
                query = f"SELECT * FROM {self.table_name} WHERE {column_name} = ?"
                result = self.connection.execute(query, (value,))
                self.tableWidget.setRowCount(0)
                for row_number, row_data in enumerate(result):
                    self.tableWidget.insertRow(row_number)
                    for column_number, data in enumerate(row_data):
                        self.tableWidget.setItem(row_number, column_number, QTableWidgetItem(str(data)))
            else:
                QMessageBox.warning(self, "Warning", f"Column {column_name} does not exist")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
