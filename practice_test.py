from PyQt5.QtWidgets import QApplication,QWidget,QPushButton,QVBoxLayout,QHBoxLayout,QLabel,QFrame
import sys
import sip
NetworkLbel_style = '''
    QLabel#main{background-color:red;}
    QLabel > QLabel{border-top-left-radius:5px;
                    border-top-right-radius:5px;
                    background-color:white;
                    border-style:none solid;}
    QPushButton{background-color:transparent;
                }
    QPushButton:hover{background-color:gray}
'''
class NetworkLabel(QLabel):
    def __init__(self,parent):
        super().__init__()
        if parent:
            self.setParent(parent)
        self.setGeometry(300,300,900,30)
        self.num        =   0
        self.label_num  = 20
        self.config     =   {}
        self.currentlab = ""
        self.setObjectName("main")
        self.setStyleSheet(NetworkLbel_style)
        self.main_layout= QHBoxLayout()
        self.main_layout.setContentsMargins(0,1,0,1)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)
        self.show()

    def addlabel(self,label:QLabel):
        self.num += 1
        label.setParent(self)
        self.currentlab = "label"+str(self.num)
        self.config[self.currentlab] = {}
        self.config[self.currentlab]["widget"] = label

    def set_first_btn(self,btn:QPushButton):
        self.config[self.currentlab]["firstbtn"] = btn

    def set_close_btn(self,btn:QPushButton):
        self.config[self.currentlab]["closebtn"] =  btn
        btn.clicked.connect(self.close_btn_label_close)

    def close_btn_label_close(self):
        self.num -= 1
        self.sender().parent().close()
        for s in self.config.keys():
            if self.config[s]["closebtn"] == self.sender():
                del self.config[s]
                break
        self.add_layout()

    def add_layout(self):
        print(self.config)
        for s in self.children():
            if s.isWidgetType():
                self.main_layout.removeWidget(s)
        for d in self.config.keys():
            self.main_layout.addWidget(self.config[d]["widget"],1)
        if self.num < self.label_num:
            self.main_layout.addWidget(QFrame(self),self.label_num-self.num)

class MyUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100,100,900,800)
        self.addbtn = QPushButton("add",self)
        self.addbtn.clicked.connect(self.add_btn_clcked)
        self.label = NetworkLabel(self)
        self.label.label_num = 10
        self.buttom = QFrame(self)
        self.mainlayout = QVBoxLayout()
        self.setLayout(self.mainlayout)
        self.mainlayout.addWidget(self.addbtn,1)
        self.mainlayout.addWidget(self.label,1)
        self.mainlayout.addWidget(self.buttom,30)
        self.mainlayout.setSpacing(0)
        self.mainlayout.setContentsMargins(0,0,0,0)
        self.show()

    def add_btn_clcked(self):
        label = QLabel(self)
        btn1 = QPushButton("添加",self)
        btn2 = QPushButton("x",self)
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        label.setLayout(layout)
        layout.addWidget(btn1,4)
        layout.addWidget(btn2,1)
        self.label.addlabel(label)
        self.label.set_close_btn(btn2)
        self.label.add_layout()



if  __name__ == "__main__":
    app = QApplication(sys.argv)
    s = MyUI()
    app.exec_()