from dataclasses import dataclass

from PySide2 import QtCore, QtGui, QtWidgets

class Dialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.field_x = QtWidgets.QSpinBox()
        self.field_y = QtWidgets.QSpinBox()
        self.field_z = QtWidgets.QSpinBox()
        self.button = QtWidgets.QPushButton('coucou')

        layout.addWidget(self.field_x)
        layout.addWidget(self.field_y)
        layout.addWidget(self.field_z)
        layout.addWidget(self.button)

        self.button.clicked.connect(self.create_instance)

    def get_data(self):
        dic = {'x':self.field_x.value(),
               'y':self.field_x.value(),
               'z':self.field_x.value()}

        return dic

    def create_instance(self):
        data_a = DataA(**self.get_data())
        a = A(data_a)

@dataclass
class DataA:
    x:int
    y:int
    z:int

class A:
    def __init__(self, data:DataA):
        self.data = data
        print('coucou')

ui = Dialog()
ui.show()
