import sys
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QIcon, QPainter
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCharts import QChart, QChartView, QXYSeries, QLineSeries
import pyqtgraph as pg

import time
import threading

class posArray:
    def __init__(self):
        self.x = [];
        self.y = [];
        self.t = [];

class UGVData:
    def __init__(self):
        self.posAct = posArray();
        self.posExp = posArray();
        self.posError = posArray();
        self.vAct = [];
        self.vExp = [];
        self.headAct = [];
        self.headExp = [];


    def clearData(self):
        self.posAct = posArray();
        self.posExp = posArray();
        self.vAct = [];
        self.vExp = [];
        self.headAct = [];
        self.headExp = [];


class UGVToolingBenchWindow(QMainWindow):
    position_actual = Signal(str);
    position_expected = Signal(str);

    def __init__(self):
        super().__init__();
        self.setWindowTitle("UGV Dashboard");
        self.__main = QWidget();
        self.setCentralWidget(self.__main);

        self.connectButton = QPushButton();
        self.connectButton.clicked.connect(self.startConnection);

        self.title = QLabel("UGV Dashboard");
        
        self.UGVData = UGVData();

        self.tabs = QTabWidget();
        self.tabs.addTab(PathTab(self), "Path");

        self.motorPage = QWidget();
        self.motorPageLayout = QVBoxLayout(self.motorPage);
        self.tabs.addTab(self.motorPage, "Motor Dashboard");

        self.mainLayout = QVBoxLayout(self.__main);
        self.mainLayout.addWidget(self.title);
        self.mainLayout.addWidget(self.tabs);

        self.showMaximized();

    @Slot()
    def startConnection(self):
        self.connectButton.setText("Connecting");
        self.connectButton.setEnabled(False);
        self.connectButton.repaint();
        success = self.connectToUGV();
        if(success):
            self.connectButton.setText("Re-Connect");
        else:
            self.connectButton.setText("Failed to Connect");
            
        self.connectButton.setEnabled(True);

    def connectToUGV(self):
        x = threading.Thread(target=self.connectAndPoll, daemon=True);
        x.start();
        time.sleep(2);
        return True;
    
    def connectAndPoll(self):
        posActFile = open("position_actual.csv", "r");
        posExpFile = open("position_expected.csv", "r");
        posAct = "Init";
        while(posAct):
            posAct = posActFile.readline();
            self.position_actual.emit(posAct)
            posExp = posExpFile.readline();
            self.position_expected.emit(posExp);
            time.sleep(5);
            

class PathTab(QWidget):
    def __init__(self, parent:UGVToolingBenchWindow):
        super().__init__(parent);

        self.UGVData = parent.UGVData;

        self.clearDataButton = QPushButton();
        self.clearDataButton.setText("Clear Data");
        self.clearDataButton.clicked.connect(self.clearData);

        parent.connectButton.setText("Connect");

        self.rTitle = QLabel("Right Title");
        self.lTitle = QLabel("Left Title");

        self.actPen = pg.mkPen(color=(255,0,0));
        self.expPen = pg.mkPen(color=(0,255,0));

        self.posPlot = pg.PlotWidget();
        self.posPlot.setBackground('w');

        self.posActCurve = self.posPlot.plot(parent.UGVData.posAct.x, parent.UGVData.posAct.y, pen=self.actPen);
        self.posExpCurve = self.posPlot.plot(parent.UGVData.posExp.x, parent.UGVData.posExp.y, pen=self.expPen);

        self.posErrorCloud = pg.PlotWidget();
        self.posErrorCloud.setBackground('w');

        self.posErrorPoints = self.posErrorCloud.plot(parent.UGVData.posError.x, parent.UGVData.posError.y, pen=None, symbol="o", symbolPen=self.actPen, symbolSize=2);

        self.plotTabs = QTabWidget();
        self.plotTabs.addTab(self.posPlot, "UGV Position Path");
        self.plotTabs.addTab(self.posErrorCloud, "UGV Position Cloud");

        self.lLayout = QVBoxLayout();
        self.lLayout.addWidget(self.lTitle);
        self.lLayout.addWidget(parent.connectButton);
        self.lLayout.addWidget(self.plotTabs);
        self.lLayout.addWidget(self.clearDataButton);

        self.rLayout = QVBoxLayout();
        self.rLayout.addWidget(self.rTitle);

        self.pathPageLayout = QHBoxLayout();
        self.pathPageLayout.addLayout(self.lLayout, 50);
        self.pathPageLayout.addLayout(self.rLayout, 50);

        self.setLayout(self.pathPageLayout);
    
        parent.position_actual.connect(self.addPointToPathAct);
        parent.position_expected.connect(self.addPointToPathExp);

    @Slot()
    def clearData(self):
        self.UGVData.clearData();

    @Slot(str)
    def addPointToPathAct(self, value:str):
        print(self.UGVData.posError.x);
        valArray = value.split(',');
        if(len(valArray) > 2):
            # self.posActSeries.append(valArray[1], valArray[2]);
            self.UGVData.posAct.t.append(float(valArray[0]));
            self.UGVData.posAct.x.append(float(valArray[1]));
            self.UGVData.posAct.y.append(float(valArray[2]));
            self.posActCurve.setData(self.UGVData.posAct.x, self.UGVData.posAct.y);
            if(float(valArray[0]) in self.UGVData.posExp.t):
                i = self.UGVData.posExp.t.index(float(valArray[0]));
                self.UGVData.posError.t.append(float(valArray[0]));
                self.UGVData.posError.x.append(float(valArray[1]) - self.UGVData.posExp.x[i]);
                self.UGVData.posError.y.append(float(valArray[2]) - self.UGVData.posExp.y[i]);
                self.posErrorPoints.setData(self.UGVData.posError.x, self.UGVData.posError.y);

    @Slot(str)
    def addPointToPathExp(self, value):
        valArray = value.split(',');
        if(len(valArray) > 2):
            # self.posExpSeries.append(valArray[1], valArray[2]);
            self.UGVData.posExp.t.append(float(valArray[0]));
            self.UGVData.posExp.x.append(float(valArray[1]));
            self.UGVData.posExp.y.append(float(valArray[2]));
            self.posExpCurve.setData(self.UGVData.posExp.x, self.UGVData.posExp.y);
            if(float(valArray[0]) in self.UGVData.posAct.t):
                i = self.UGVData.posAct.t.index(float(valArray[0]));
                self.UGVData.posError.t.append(float(valArray[0]));
                self.UGVData.posError.x.append(self.UGVData.posAct.x[i] - float(valArray[1]));
                self.UGVData.posError.y.append(self.UGVData.posAct.y[i] - float(valArray[2]));
                self.posErrorPoints.setData(self.UGVData.posError.x, self.UGVData.posError.y);


def main():
    toolingApplication = QApplication([]);
    toolingWindow = UGVToolingBenchWindow();
    toolingWindow.show();
    sys.exit(toolingApplication.exec());



if __name__ == "__main__":
    main()