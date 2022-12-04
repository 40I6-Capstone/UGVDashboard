import sys
from PySide6.QtWidgets import QApplication
from UGVToolingBenchWindow import UGVToolingBenchWindow


def main():
    toolingApplication = QApplication([]);
    toolingWindow = UGVToolingBenchWindow();
    toolingWindow.show();
    sys.exit(toolingApplication.exec());



if __name__ == "__main__":
    main()