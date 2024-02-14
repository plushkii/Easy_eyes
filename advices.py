import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QWidget


class AdviceForm(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('UI/advises.ui', self)
        self.initUI()

    def initUI(self):
        self.read()

    def read(self):
        file = open('data/advice.txt', encoding='utf8')
        txt = file.read()
        self.textEdit.setPlainText(txt)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AdviceForm()
    ex.show()
    sys.exit(app.exec())
