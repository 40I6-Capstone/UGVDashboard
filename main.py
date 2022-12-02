import sys
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QIcon, QPainter
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCharts import QChart, QChartView, QXYSeries, QLineSeries
import pyqtgraph as pg

import numpy
import time
import threading

class posArray:
    def __init__(self):
        self.x = [];
        self.y = [];
        self.t = [];
                 
class dataArray:
    def __init__(self):
        self.data = [];
        self.t = [];


class UGVData:
    def __init__(self):
        self.posAct = posArray();
        self.posExp = posArray();
        self.vAct = dataArray();
        self.vExp = dataArray();
        self.headAct = dataArray();
        self.headExp = dataArray();

    def clearData(self):
        self.posAct = posArray();
        self.posExp = posArray();
        self.vAct = dataArray();
        self.vExp = dataArray();
        self.headAct = dataArray();
        self.headExp = dataArray();
    
def truncateData(dataSet:dataArray):
    if(dataSet.t[-1]-dataSet.t[0]>10):
        dataSet.t = dataSet.t[1:];
        dataSet.data = dataSet.data[1:];

class UGVToolingBenchWindow(QMainWindow):
    posActSignal = Signal(str);
    posExpSignal = Signal(str);
    vActSignal = Signal(str);
    vExpSignal = Signal(str);
    headActSignal = Signal(str);
    headExpSignal = Signal(str);

    def __init__(self):
        super().__init__();
        self.setWindowTitle("UGV Dashboard");
        self.__main = QWidget();
        self.setCentralWidget(self.__main);
        self.setStyleSheet(open('stylesheet.qss').read());

        self.connectButton = QPushButton();
        self.connectButton.clicked.connect(self.startConnection);
        self.connectionActive = False;

        self.title = QLabel("UGV Dashboard");
        self.title.setObjectName("Title");
        
        self.UGVData = UGVData();

        self.tabs = QTabWidget();
        self.tabs.setObjectName("MainTab")
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
        if(self.connectButton.text() == "Disconnect"):
            self.connectButton.setText("Connect");
            self.connectionActive = False;
        else:    
            self.connectButton.setText("Connecting");
            self.connectButton.setEnabled(False);
            self.connectButton.repaint();
            self.connectionActive = True;
            success = self.connectToUGV();
            if(success):
                self.connectButton.setText("Disconnect");
            else:
                self.connectButton.setText("Connect");
                self.connectionActive = False;
                
            self.connectButton.setEnabled(True);

    def connectToUGV(self):
        self.ugvConnectionThread = threading.Thread(target=self.connectAndPoll, daemon=True);
        self.ugvConnectionThread.start();
        time.sleep(2);
        return True;
    
    def connectAndPoll(self):
        vHeadActFile = open("velocity_heading_actual.csv", "r");
        vHeadExpFile = open("velocity_heading_expected.csv", "r");
        posActFile = open("position_actual.csv", "r");
        posExpFile = open("position_expected.csv", "r");
        while(self.connectionActive):
            vHAct = vHeadActFile.readline();
            vHAct = vHAct.split(',');
            if(len(vHAct)>2):
                self.vActSignal.emit(vHAct[0]+","+vHAct[1]);
                self.headActSignal.emit(vHAct[0]+","+vHAct[2]);
            vHExp = vHeadExpFile.readline();
            vHExp = vHExp.split(',');
            if(len(vHExp)>2):
                self.vExpSignal.emit(vHExp[0]+","+vHExp[1]);
                self.headExpSignal.emit(vHExp[0]+","+vHExp[2]);
            posAct = posActFile.readline();
            posAct = posAct.split(',');
            if(len(posAct)>2):
                self.posActSignal.emit(posAct[0]+","+posAct[1]+","+posAct[2]);
            posExp = posExpFile.readline();
            posExp = posExp.split(',');
            if(len(posExp)>2):
                self.posExpSignal.emit(posExp[0]+","+posExp[1]+","+posExp[2]);

            time.sleep(1);
            

class PathTab(QWidget):
    def __init__(self, parent:UGVToolingBenchWindow):
        super().__init__(parent);

        self.UGVData = parent.UGVData;

        self.clearDataButton = QPushButton();
        self.clearDataButton.setText("Clear Data");
        self.clearDataButton.clicked.connect(self.clearData);

        parent.connectButton.setText("Connect");

        self.actPen = pg.mkPen(color=(255,0,0), width=5);
        self.expPen = pg.mkPen(color=(0,0,255), width=5);

        self.posPlot = pg.PlotWidget();
        self.posPlot.setBackground("#435058");
        self.posPlot.addLegend();
        self.posPlot.setLabel('left', 'Y position');
        self.posPlot.setLabel('bottom', 'X Position');

        self.posActCurve = self.posPlot.plot(parent.UGVData.posAct.x, parent.UGVData.posAct.y, name="Position Actual", pen=self.actPen);
        self.posExpCurve = self.posPlot.plot(parent.UGVData.posExp.x, parent.UGVData.posExp.y, name="Position Expected", pen=self.expPen);

        self.posCloud = pg.PlotWidget();
        self.posCloud.setBackground("#435058");

        self.posActPoints = self.posCloud.plot(parent.UGVData.posAct.x, parent.UGVData.posAct.y, pen=None, symbol="+", symbolPen=self.actPen, symbolSize=5);
        self.posExpPoints = self.posCloud.plot(parent.UGVData.posExp.x, parent.UGVData.posExp.y, pen=None, symbol="+", symbolPen=self.expPen, symbolSize=5);

        self.plotTabs = QTabWidget();
        self.plotTabs.setObjectName("SubPageTabs")
        self.plotTabs.addTab(self.posPlot, "UGV Position Path");
        self.plotTabs.addTab(self.posCloud, "UGV Position Cloud");

        self.lLayout = QVBoxLayout();
        self.lLayout.addWidget(parent.connectButton);
        self.lLayout.addWidget(self.plotTabs);
        self.lLayout.addWidget(self.clearDataButton);

        self.vPlot = pg.PlotWidget();
        self.vPlot.setBackground("#435058");
        self.vActCurve = self.vPlot.plot(parent.UGVData.vAct.t, parent.UGVData.vAct.data, pen=self.actPen);
        self.vExpCurve = self.vPlot.plot(parent.UGVData.vExp.t, parent.UGVData.vExp.data, pen=self.expPen);

        self.headPlot = pg.PlotWidget();
        self.headPlot.setBackground("#435058");
        self.headActCurve = self.headPlot.plot(parent.UGVData.headAct.t, parent.UGVData.headAct.data, pen=self.actPen);
        self.headExpCurve = self.headPlot.plot(parent.UGVData.headExp.t, parent.UGVData.headExp.data, pen=self.expPen);

        vHeader = QLabel("Velocity of UGV");
        vHeader.setObjectName("PlotHeader");
        hHeader = QLabel("Heading of UGV");
        hHeader.setObjectName("PlotHeader");

        self.rLayout = QVBoxLayout();
        self.rLayout.addWidget(vHeader);
        self.rLayout.addWidget(self.vPlot);
        self.rLayout.addWidget(hHeader);
        self.rLayout.addWidget(self.headPlot);

        self.pathPageLayout = QHBoxLayout();
        self.pathPageLayout.addLayout(self.lLayout, 50);
        self.pathPageLayout.addLayout(self.rLayout, 50);

        self.setLayout(self.pathPageLayout);

        parent.posActSignal.connect(self.addPointToPathAct);
        parent.posExpSignal.connect(self.addPointToPathExp);
        parent.vActSignal.connect(self.addPointToVAct);
        parent.vExpSignal.connect(self.addPointToVExp);
        parent.headActSignal.connect(self.addPointToHeadAct);
        parent.headExpSignal.connect(self.addPointToHeadExp);

    @Slot()
    def clearData(self):
        self.UGVData.clearData();
        self.posActPoints.setData([],[]);
        self.posExpPoints.setData([],[]);
        self.vActCurve.setData([],[]);
        self.vExpCurve.setData([],[]);
        self.headActCurve.setData([],[]);
        self.headExpCurve.setData([],[]);

    @Slot(str)
    def addPointToPathAct(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.posAct.t.append(float(valArray[0]));
            self.UGVData.posAct.x.append(float(valArray[1]));
            self.UGVData.posAct.y.append(float(valArray[2]));
            self.posActCurve.setData(self.UGVData.posAct.x, self.UGVData.posAct.y);
            self.posActPoints.setData(self.UGVData.posAct.x, self.UGVData.posAct.y);
    
    @Slot(str)
    def addPointToPathExp(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.posExp.t.append(float(valArray[0]));
            self.UGVData.posExp.x.append(float(valArray[1]));
            self.UGVData.posExp.y.append(float(valArray[2]));
            self.posExpCurve.setData(self.UGVData.posExp.x, self.UGVData.posExp.y);
            self.posExpPoints.setData(self.UGVData.posExp.x, self.UGVData.posExp.y);

    @Slot(str)
    def addPointToVAct(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.vAct.t.append(float(valArray[0]));
            self.UGVData.vAct.data.append(float(valArray[1]));
            truncateData(self.UGVData.vAct);
            self.vActCurve.setData(self.UGVData.vAct.t, self.UGVData.vAct.data);
    
    @Slot(str)
    def addPointToVExp(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.vExp.t.append(float(valArray[0]));
            self.UGVData.vExp.data.append(float(valArray[1]));
            truncateData(self.UGVData.vExp);
            self.vExpCurve.setData(self.UGVData.vExp.t, self.UGVData.vExp.data);

    @Slot(str)
    def addPointToHeadAct(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.headAct.t.append(float(valArray[0]));
            self.UGVData.headAct.data.append(float(valArray[1]));
            truncateData(self.UGVData.headAct);
            self.headActCurve.setData(self.UGVData.headAct.t, self.UGVData.headAct.data);

    
    @Slot(str)
    def addPointToHeadExp(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.headExp.t.append(float(valArray[0]));
            self.UGVData.headExp.data.append(float(valArray[1]));
            truncateData(self.UGVData.headExp);
            self.headExpCurve.setData(self.UGVData.headExp.t, self.UGVData.headExp.data);

            


def main():
    toolingApplication = QApplication([]);
    toolingWindow = UGVToolingBenchWindow();
    toolingWindow.show();
    sys.exit(toolingApplication.exec());



if __name__ == "__main__":
    main()