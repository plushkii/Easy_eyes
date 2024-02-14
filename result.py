import sqlite3
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QInputDialog


class Results(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("UI/results.ui", self)
        self.con = sqlite3.connect("Eyes_data.sqlite")
        self.pushButton.clicked.connect(self.delete_elem)
        self.pushButton_2.clicked.connect(self.update_result)
        self.pushButton_3.clicked.connect(self.save_results)
        self.tableWidget.itemChanged.connect(self.item_changed)
        self.modified = {}
        self.titles = None
        cur = self.con.cursor()
        # Получили результат запроса, который ввели в текстовое поле
        result = cur.execute("SELECT * FROM result").fetchall()
        # Заполнили размеры таблицы
        self.tableWidget.setRowCount(len(result))
        # Если запись не нашлась, то не будем ничего делать
        self.tableWidget.setColumnCount(len(result[0]))
        self.titles = [description[0] for description in cur.description]
        # Заполнили таблицу полученными элементами
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))

    def update_result(self):
        cur = self.con.cursor()
        item_data = self.textEdit.toPlainText().strip()  # Убираем лишние пробелы
        if item_data:
            # Если запрос не пустой, выполните поиск по дате
            result = cur.execute("SELECT * FROM result WHERE data=?", (item_data,)).fetchall()
            self.statusBar().clearMessage()
        else:
            # Если запрос пустой, выведите все элементы
            result = cur.execute("SELECT * FROM result").fetchall()
            self.statusBar().clearMessage()

        self.tableWidget.setRowCount(len(result))
        if not result:
            self.statusBar().showMessage('Ничего не нашлось')
            return
        else:
            self.statusBar().showMessage(f"Найдено записей: {len(result)}")

        self.tableWidget.setColumnCount(len(result[0]))
        self.titles = [description[0] for description in cur.description]

        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(val)))

                self.modified = {}

    def item_changed(self, item):
        # Если значение в ячейке было изменено,
        # то в словарь записывается пара: название поля, новое значение
        self.modified[self.titles[item.column()]] = item.text()

    def save_results(self):
        if self.modified:
            cur = self.con.cursor()
            que = "UPDATE result SET\n"
            que += ", ".join([f"{key}='{self.modified.get(key)}'"
                              for key in self.modified.keys()])
            que += "WHERE data = ?"
            print(que)
            cur.execute(que, (self.textEdit.toPlainText(),))
            self.con.commit()
            self.modified.clear()

    def delete_elem(self):
        # Получаем список элементов без повторов и их id
        rows = list(set([i.row() for i in self.tableWidget.selectedItems()]))
        dates = [self.tableWidget.item(i, 0).text() for i in rows]
        # Спрашиваем у пользователя подтверждение на удаление элементов
        valid = QMessageBox.question(
            self, '', "Действительно удалить элементы с id " + ",".join(dates),
            QMessageBox.Yes, QMessageBox.No)
        # Если пользователь ответил утвердительно, удаляем элементы.
        # Не забываем зафиксировать изменения
        if valid == QMessageBox.Yes:
            cur = self.con.cursor()
            cur.execute("DELETE FROM result WHERE id IN (" + ", ".join(
                '?' * len(dates)) + ")", dates)
            self.con.commit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Results()
    ex.show()
    sys.exit(app.exec())
