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
        self.posError = posArray();
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

def calculateActPosition(data:UGVData):
    if(len(data.vAct.t)==1):
        data.posAct.t.append(data.vAct.t[0]);
        data.posAct.x.append(0);
        data.posAct.y.append(0);
    else:
        t1 = data.vAct.t[-1];
        t2 = data.vAct.t[-2];
        vx1 = data.vAct.data[-1]*numpy.cos(data.headAct.data[-1]*numpy.pi/180);
        vx2 = data.vAct.data[-2]*numpy.cos(data.headAct.data[-2]*numpy.pi/180);
        vy1 = data.vAct.data[-1]*numpy.sin(data.headAct.data[-1]*numpy.pi/180);
        vy2 = data.vAct.data[-2]*numpy.sin(data.headAct.data[-2]*numpy.pi/180);
        posX = data.posAct.x[-1] + numpy.abs(vx1-vx2)*(t1-t2)/2 + numpy.min([vx1, vx2])*(t1-t2);
        posY = data.posAct.y[-1] + numpy.abs(vy1-vy2)*(t1-t2)/2 + numpy.min([vy1, vy2])*(t1-t2);
        data.posAct.t.append(t1);
        data.posAct.x.append(posX);
        data.posAct.y.append(posY);

def calculateExpPosition(data:UGVData):
    if(len(data.vExp.t)==1):
        data.posExp.t.append(data.vAct.t[0]);
        data.posExp.x.append(0);
        data.posExp.y.append(0);
    else:
        t1 = data.vExp.t[-1];
        t2 = data.vExp.t[-2];
        vx1 = data.vExp.data[-1]*numpy.cos(data.headExp.data[-1]*numpy.pi/180);
        vx2 = data.vExp.data[-2]*numpy.cos(data.headExp.data[-2]*numpy.pi/180);
        vy1 = data.vExp.data[-1]*numpy.sin(data.headExp.data[-1]*numpy.pi/180);
        vy2 = data.vExp.data[-2]*numpy.sin(data.headExp.data[-2]*numpy.pi/180);
        posX = data.posExp.x[-1] + numpy.abs(vx1-vx2)*(t1-t2)/2 + numpy.min([vx1, vx2])*(t1-t2);
        posY = data.posExp.y[-1] + numpy.abs(vy1-vy2)*(t1-t2)/2 + numpy.min([vy1, vy2])*(t1-t2);
        data.posExp.t.append(t1);
        data.posExp.x.append(posX);
        data.posExp.y.append(posY);
    


class UGVToolingBenchWindow(QMainWindow):
    posActSignal = Signal();
    posExpSignal = Signal();
    vActSignal = Signal(str);
    vExpSignal = Signal(str);
    headActSignal = Signal(str);
    headExpSignal = Signal(str);

    def __init__(self):
        super().__init__();
        self.setWindowTitle("UGV Dashboard");
        self.__main = QWidget();
        self.setCentralWidget(self.__main);
        self.setStyleSheet(open('stylesheet.css').read());

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

        self.posActCurve = self.posPlot.plot(parent.UGVData.posAct.x, parent.UGVData.posAct.y, pen=self.actPen);
        self.posExpCurve = self.posPlot.plot(parent.UGVData.posExp.x, parent.UGVData.posExp.y, pen=self.expPen);

        self.posErrorCloud = pg.PlotWidget();
        self.posErrorCloud.setBackground("#435058");

        self.posErrorPoints = self.posErrorCloud.plot(parent.UGVData.posError.x, parent.UGVData.posError.y, pen=None, symbol="o", symbolPen=self.actPen, symbolSize=2);

        self.plotTabs = QTabWidget();
        self.plotTabs.setObjectName("SubPageTabs")
        self.plotTabs.addTab(self.posPlot, "UGV Position Path");
        self.plotTabs.addTab(self.posErrorCloud, "UGV Position Cloud");

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
    
        self.posActSignal = parent.posActSignal;
        self.posExpSignal = parent.posExpSignal;

        parent.posActSignal.connect(self.addPointToPathAct);
        parent.posExpSignal.connect(self.addPointToPathExp);
        parent.vActSignal.connect(self.addPointToVAct);
        parent.vExpSignal.connect(self.addPointToVExp);
        parent.headActSignal.connect(self.addPointToHeadAct);
        parent.headExpSignal.connect(self.addPointToHeadExp);

    @Slot()
    def clearData(self):
        self.UGVData.clearData();
        self.posActCurve.setData([],[]);
        self.posExpCurve.setData([],[]);
        self.posErrorPoints.setData([],[]);
        self.posErrorPoints.setData([],[]);
        self.vActCurve.setData([],[]);
        self.vExpCurve.setData([],[]);
        self.headActCurve.setData([],[]);
        self.headExpCurve.setData([],[]);

    @Slot()
    def addPointToPathAct(self):
        self.posActCurve.setData(self.UGVData.posAct.x, self.UGVData.posAct.y);
        if(self.UGVData.posAct.t[-1] in self.UGVData.posExp.t):
            i = self.UGVData.posExp.t.index(self.UGVData.posAct.t[-1]);
            self.UGVData.posError.t.append(self.UGVData.posAct.t[-1]);
            self.UGVData.posError.x.append(self.UGVData.posAct.x[-1] - self.UGVData.posExp.x[i]);
            self.UGVData.posError.y.append(self.UGVData.posAct.y[-1] - self.UGVData.posExp.y[i]);
            self.posErrorPoints.setData(self.UGVData.posError.x, self.UGVData.posError.y);

    @Slot()
    def addPointToPathExp(self):
        self.posExpCurve.setData(self.UGVData.posExp.x, self.UGVData.posExp.y);
        if(self.UGVData.posExp.t[-1] in self.UGVData.posAct.t):
            i = self.UGVData.posAct.t.index(self.UGVData.posExp.t[-1]);
            self.UGVData.posError.t.append(self.UGVData.posExp.t[-1]);
            self.UGVData.posError.x.append(self.UGVData.posAct.x[i] - self.UGVData.posExp.x[-1]);
            self.UGVData.posError.y.append(self.UGVData.posAct.y[i] - self.UGVData.posExp.y[-1]);
            self.posErrorPoints.setData(self.UGVData.posError.x, self.UGVData.posError.y);

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
            calculateActPosition(self.UGVData);
            self.posActSignal.emit();

    
    @Slot(str)
    def addPointToHeadExp(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.headExp.t.append(float(valArray[0]));
            self.UGVData.headExp.data.append(float(valArray[1]));
            truncateData(self.UGVData.headExp);
            self.headExpCurve.setData(self.UGVData.headExp.t, self.UGVData.headExp.data);
            calculateExpPosition(self.UGVData);
            self.posExpSignal.emit();

            


def main():
    toolingApplication = QApplication([]);
    toolingWindow = UGVToolingBenchWindow();
    toolingWindow.show();
    sys.exit(toolingApplication.exec());



if __name__ == "__main__":
    main()