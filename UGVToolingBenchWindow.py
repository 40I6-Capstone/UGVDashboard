from PySide6.QtCore import Slot, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
import pyqtgraph as pg
import numpy as np
import time
import threading

mainColour = "#24292e"


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
        self.vRight = dataArray();
        self.vLeft = dataArray();
        self.vAvg = dataArray();
        self.dRight = dataArray();
        self.dLeft = dataArray();
        self.dAvg = dataArray();

    def clearData(self, tab: str):
        if tab == "motor":
            self.vRight = dataArray();
            self.vLeft = dataArray();
            self.vAvg = dataArray();
            self.dRight = dataArray();
            self.dLeft = dataArray();
            self.dAvg = dataArray();
        else:
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
    vRightSignal = Signal(str);
    vLeftSignal = Signal(str);
    vAverageSignal = Signal(str);
    dRightSignal = Signal(str);
    dLeftSignal = Signal(str);
    dAverageSignal = Signal(str);

    def __init__(self):
        super().__init__();
        self.setWindowTitle("UGV Dashboard");
        self.__main = QWidget();
        self.setCentralWidget(self.__main);
        styleSheet = open('stylesheet.qss').read();
        styleSheetVars = open('stylevars.txt');
        lines = styleSheetVars.readlines();
        for line in lines:
            values = line.split("=");
            styleSheet = styleSheet.replace(values[0].strip(), values[1].strip());
        
        self.setStyleSheet(styleSheet);

        self.connectButton = QPushButton();
        self.connectButton.clicked.connect(self.startConnection);
        self.connectionActive = False;

        self.title = QLabel("UGV Dashboard");
        self.title.setObjectName("Title");
        
        self.UGVData = UGVData();

        self.tabs = QTabWidget();
        self.tabs.setObjectName("MainTab")
        self.tabs.addTab(PathTab(self), "Path");
        self.tabs.addTab(MotorTab(self), "Motor Dashboard");

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

        self.settingsButton = QPushButton();
        icon = QIcon("./assets/settings.svg");
        self.settingsButton.setIcon(icon);

        buttonsLayout = QHBoxLayout();
        buttonsLayout.addWidget(parent.connectButton, 85);
        buttonsLayout.addWidget(self.settingsButton, 15)

        self.actPosPen = pg.mkPen(color=(100,0,0), width=5);
        self.expPosPen = pg.mkPen(color=(0,0, 255), width=5);
        self.outlinePen = pg.mkPen(color=(255,255,255), width=1.5);

        self.actPen = pg.mkPen(color=(255,0,0), width=5);
        self.expPen = pg.mkPen(color=(0,255, 255), width=5);

        self.posPlot = pg.PlotWidget();
        self.posPlot.setBackground(mainColour);
        self.posPlot.addLegend();
        self.posPlot.setLabel('left', 'Y position');
        self.posPlot.setLabel('bottom', 'X Position');
        self.posPlot.showGrid(x=True,y=True);

        warmColourMap = pg.colormap.getFromMatplotlib("autumn");
        self.warmColourMapTable = warmColourMap.getLookupTable(0, 1, 101);
        coolColourMap = pg.colormap.getFromMatplotlib("cool");
        self.coolColourMapTable = coolColourMap.getLookupTable(0, 1, 101);

        self.posExpCurve = self.posPlot.plot(parent.UGVData.posExp.x, parent.UGVData.posExp.y, name="Position Expected", pen=self.expPosPen, symbol="+", symbolPen=None, symbolSize=15);
        self.posActCurve = self.posPlot.plot(parent.UGVData.posAct.x, parent.UGVData.posAct.y, name="Position Actual", pen=self.actPosPen, symbol="+", symbolPen=None, symbolSize=15);

        pathHeader = QLabel("Path of UGV");
        pathHeader.setObjectName("PlotHeader");

        self.lLayout = QVBoxLayout();
        self.lLayout.addLayout(buttonsLayout);
        self.lLayout.addWidget(pathHeader);
        self.lLayout.addWidget(self.posPlot);
        self.lLayout.addWidget(self.clearDataButton);

        self.vPlot = pg.PlotWidget();
        self.vPlot.setBackground(mainColour);
        self.vPlot.addLegend();
        self.vPlot.setLabel('left', 'Velocity (m/s)');
        self.vPlot.setLabel('bottom', 'Time (s)');
        self.vPlot.showGrid(x=True,y=True);
        self.vPlot.setMouseEnabled(x=False, y=True);

        self.vExpCurve = self.vPlot.plot(parent.UGVData.vExp.t, parent.UGVData.vExp.data, pen=self.expPen, name="Expected Velocity");
        self.vActCurve = self.vPlot.plot(parent.UGVData.vAct.t, parent.UGVData.vAct.data, pen=self.actPen, name="Actual Velocity");

        self.headPlot = pg.PlotWidget();
        self.headPlot.setBackground(mainColour);
        self.headPlot.addLegend();
        self.headPlot.setLabel('left', 'Heading (deg)');
        self.headPlot.setLabel('bottom', 'Time (s)');
        self.headPlot.showGrid(x=True,y=True);
        self.headPlot.setMouseEnabled(x=False, y=True);

        self.headExpCurve = self.headPlot.plot(parent.UGVData.headExp.t, parent.UGVData.headExp.data, pen=self.expPen, name="Expected Heading");
        self.headActCurve = self.headPlot.plot(parent.UGVData.headAct.t, parent.UGVData.headAct.data, pen=self.actPen, name="Actual Heading");

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
        self.UGVData.clearData('default');
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
            linspace = np.linspace(0, 100, len(self.UGVData.posAct.t)-1).astype(int);
            brushes = self.warmColourMapTable[linspace];
            brushes = np.append(brushes, [[255,255,255]], axis=0);
            self.posActCurve.setData(self.UGVData.posAct.x, self.UGVData.posAct.y, symbolBrush=brushes);
    
    @Slot(str)
    def addPointToPathExp(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.posExp.t.append(float(valArray[0]));
            self.UGVData.posExp.x.append(float(valArray[1]));
            self.UGVData.posExp.y.append(float(valArray[2]));
            linspace = np.linspace(0, 100, len(self.UGVData.posExp.t)-1).astype(int);
            brushes = self.coolColourMapTable[linspace];
            brushes = np.append(brushes, [[255,255,255]], axis=0);
            self.posExpCurve.setData(self.UGVData.posExp.x, self.UGVData.posExp.y, symbolBrush=brushes);

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


class MotorTab(QWidget):
    def __init__(self, parent:UGVToolingBenchWindow):
        super().__init__(parent);

        self.UGVData = parent.UGVData;

        self.clearDataButton = QPushButton();
        self.clearDataButton.setText("Clear Data");
        self.clearDataButton.clicked.connect(self.clearData);

        self.rightPen = pg.mkPen(color=(255,0,0), width=5);
        self.leftPen = pg.mkPen(color=(0,255, 255), width=5);
        self.avgPen = pg.mkPen(color=(255,255, 255), width=5);

        self.vPlot = pg.PlotWidget();
        self.vPlot.setBackground(mainColour);
        self.vPlot.addLegend();
        self.vPlot.setLabel('left', 'Velocity (m/s)');
        self.vPlot.setLabel('bottom', 'Time (s)');
        self.vPlot.showGrid(x=True,y=True);
        self.vPlot.setMouseEnabled(x=False, y=True);

        self.vAvgCurve = self.vPlot.plot(parent.UGVData.vAvg.t, parent.UGVData.vAvg.data, pen=self.avgPen, name="Average Velocity");
        self.vRightCurve = self.vPlot.plot(parent.UGVData.vRight.t, parent.UGVData.vRight.data, pen=self.rightPen, name="Right Motor Velocity");
        self.vLeftCurve = self.vPlot.plot(parent.UGVData.vLeft.t, parent.UGVData.vLeft.data, pen=self.leftPen, name="Left Motor Velocity");

        self.distPlot = pg.PlotWidget();
        self.distPlot.setBackground(mainColour);
        self.distPlot.addLegend();
        self.distPlot.setLabel('left', 'Distance (m)');
        self.distPlot.setLabel('bottom', 'Time (s)');
        self.distPlot.showGrid(x=True,y=True);
        self.distPlot.setMouseEnabled(x=False, y=True);

        self.dAvgCurve = self.distPlot.plot(parent.UGVData.dAvg.t, parent.UGVData.dAvg.data, pen=self.avgPen, name="Average Distance");
        self.dRightCurve = self.distPlot.plot(parent.UGVData.dRight.t, parent.UGVData.dRight.data, pen=self.rightPen, name="Right Distance");
        self.dLeftCurve = self.distPlot.plot(parent.UGVData.headAct.t, parent.UGVData.headAct.data, pen=self.leftPen, name="Left Motor Distance");


        self.plotTabs = QTabWidget();
        self.plotTabs.setObjectName("SubPageTabs")
        self.plotTabs.addTab(self.vPlot, "Motor Velocity");
        self.plotTabs.addTab(self.distPlot, "Motor Distance Traveled");

        self.pathPageLayout = QVBoxLayout();
        self.pathPageLayout.addWidget(self.plotTabs);
        self.pathPageLayout.addWidget(self.clearDataButton);

        self.setLayout(self.pathPageLayout);

        parent.vAverageSignal.connect(self.addPointToVAvg);
        parent.vRightSignal.connect(self.addPointToVRight);
        parent.vLeftSignal.connect(self.addPointToVLeft);
        parent.dAverageSignal.connect(self.addPointToDAvg);
        parent.dRightSignal.connect(self.addPointToDRight);
        parent.dLeftSignal.connect(self.addPointToDLeft);

    @Slot()
    def clearData(self):
        self.UGVData.clearData('motor');
        self.vAvgCurve.setData([],[]);
        self.vRightCurve.setData([],[]);
        self.vLeftCurve.setData([],[]);
        self.dAvgCurve.setData([],[]);
        self.dRightCurve.setData([],[]);
        self.dLeftCurve.setData([],[]);

    @Slot(str)
    def addPointToVAvg(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.vAvg.t.append(float(valArray[0]));
            self.UGVData.vAvg.data.append(float(valArray[1]));
            truncateData(self.UGVData.vAvg);
            self.vAvgCurve.setData(self.UGVData.vAvg.t, self.UGVData.vAvg.data);

    @Slot(str)
    def addPointToVRight(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.vRight.t.append(float(valArray[0]));
            self.UGVData.vRight.data.append(float(valArray[1]));
            truncateData(self.UGVData.vRight);
            self.vRightCurve.setData(self.UGVData.vRight.t, self.UGVData.vRight.data);
    
    @Slot(str)
    def addPointToVLeft(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.vLeft.t.append(float(valArray[0]));
            self.UGVData.vLeft.data.append(float(valArray[1]));
            truncateData(self.UGVData.vLeft);
            self.vLeftCurve.setData(self.UGVData.vLeft.t, self.UGVData.vLeft.data);

    @Slot(str)
    def addPointToDAvg(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.dAvg.t.append(float(valArray[0]));
            self.UGVData.dAvg.data.append(float(valArray[1]));
            truncateData(self.UGVData.dAvg);
            self.dAvgCurve.setData(self.UGVData.dAvg.t, self.UGVData.dAvg.data);

    @Slot(str)
    def addPointToDRight(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.dRight.t.append(float(valArray[0]));
            self.UGVData.dRight.data.append(float(valArray[1]));
            truncateData(self.UGVData.dRight);
            self.dRightCurve.setData(self.UGVData.dRight.t, self.UGVData.dRight.data);
    
    @Slot(str)
    def addPointToDLeft(self, value):
        valArray = value.split(',');
        if(len(valArray) > 1):
            self.UGVData.dLeft.t.append(float(valArray[0]));
            self.UGVData.dLeft.data.append(float(valArray[1]));
            truncateData(self.UGVData.dLeft);
            self.dLeftCurve.setData(self.UGVData.dLeft.t, self.UGVData.dLeft.data);