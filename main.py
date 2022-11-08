import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

class UGVToolingBenchWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UGV Tooling Bench")
        self.showMaximized()

def main():
    toolingApplication = QApplication([])
    toolingWindow = UGVToolingBenchWindow()
    toolingWindow.show()
    sys.exit(toolingApplication.exec())

if __name__ == "__main__":
    main()