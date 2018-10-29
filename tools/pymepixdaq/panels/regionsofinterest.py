import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui


class BaseItem(QtCore.QObject):

    def __init__(self,parent=None):
        QtCore.QObject.__init__(self)
        self._parent = parent
        self._data = ['','','']
        self._children = []

    def addChild(self,item):
        self._children.append(item)

    def removeChild(self,index):
        self._children.pop(index)

    def child(self,row):
        if row < self.childCount():
            return self._children[row]
        return None

    @property
    def columnName(self):
        return self._data[0]

    @columnName.setter
    def columnName(self,value):
        self._data[0] = value

    @property
    def columnStart(self):
        return self._data[1]

    @columnStart.setter
    def columnStart(self,value):
        self._data[1] = value

    @property
    def columnEnd(self):
        return self._data[2]

    @columnEnd.setter
    def columnEnd(self,value):
        self._data[2] = value


    def childCount(self):
        return len(self._children)


    def row(self):
        if self._parent:
            return self._parent._children.index(self)
        return 0

    def columnCount(self):
        return len(self._data)

    def data(self,column):
        if column < self.columnCount():
            return self._data[column]
        return None

    def parentItem(self):
        return self._parent

    def clearChildren(self):
        for child in self._children:
            child._parent=None

        for x in range(self.childCount()):
            self.removeChild(0)

class RoiItem(BaseItem):

    roiUpdated = QtCore.pyqtSignal(str,float,float)
    roiRemoved = QtCore.pyqtSignal(str)


    def __init__(self,name,start_region,end_region,color=None):
        self._name = name
        self._start_region = start_region
        self._end_region = end_region

        self._roi_item = pg.LinearRegionItem(values = [self._start_region,self._end_region],brush=color)

        self._data = [self._name,str(self._start_region*1E6),str(self._end_region*1E6)]
        self._roi_item.sigRegionChangeFinished.connect(self.onUserUpdateRoi)

    def onUserUpdateRoi(self):
        self._start_region,self._end_region = self._roi_item.getRegion()

        self._data = [self._name,str(self._start_region*1E6),str(self._end_region*1E6)]

        self.roiUpdated.emit(self._name,self._start_region,self._end_region)

    @property
    def RoiPlotItem(self):
        return self._roi_item
    
    def onRemove(self):
        self.roiRemoved.emit()






class RoiModel(QtCore.QAbstractItemModel):


    modelChanged = QtCore.pyqtSignal()

    def __init__(self,parent=None):
        QtCore.QAbstractItemModel.__init__(self,parent)
        self.rootItem = BaseItem()
        self.rootItem._data = ['Name','Start','End']
    def headerData(self,section, orientation,role):
        if orientation == QtGui.Qt.Horizontal and role == QtGui.Qt.DisplayRole:
            return self.rootItem.data(section)

        return QtCore.QVariant()


    def index(self,row,column,parent):

        if self.hasIndex(row, column, parent) == False:
            return QtCore.QtCore.QModelIndex()

        parentItem = None

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()



        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self,index):

        if  not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parentItem()

        if (parentItem == self.rootItem):
            return QtCore.QModelIndex()
        if parentItem == None:
            return QtCore.QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)


    def rowCount(self,parent):


        if (parent.column() > 0):
            return 0

        if ( not parent.isValid()):
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def columnCount(self,parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self,index,role):
        if (not index.isValid()):
            return QtCore.QVariant()

        if (role != QtCore.Qt.DisplayRole):
            return QtCore.QVariant()

        item = index.internalPointer()

        value = item.data(index.column())
        if not value:
            return QtCore.QVariant()

        return value


    def searchItem(self,search_term):

        for child in self.rootItem.children:
            if child.columnName == search_term:
                return child
        return None
