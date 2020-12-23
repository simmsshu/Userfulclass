import requests,re,json,time
from PyQt5.QtWidgets import QLabel,QApplication,QLineEdit,QTableWidgetItem,QFrame,QAbstractItemView,QPushButton,QTextEdit
from PyQt5.QtGui import QMovie,QIcon,QColor,QMouseEvent,QPaintEvent,QPainter,QBrush
from PyQt5.Qt import QThread,QHBoxLayout,QGridLayout,QVBoxLayout,QPixmap,QFont
from PyQt5.QtCore import pyqtSignal,Qt,QModelIndex,QRect,QPoint
from PyQt5.QtWidgets import QTableWidget,QAbstractItemView,QWidget
from multiprocessing import Process
from datetime import datetime,timedelta
from elasticsearch import Elasticsearch
from bson import ObjectId
import logging
import sys
import importlib
logging.basicConfig(level= logging.DEBUG)
PIC_BASE_DIR = "../SOURCES/pic/"
pressFlag = -1
#获取当前屏幕
def get_current_screen_desktop():
    return QApplication.desktop().screen(QApplication.desktop().screenNumber())

def add_uncertain_data(data,number,sourlist = [],sourcedict = {}):
    '''
    :param data: 字典数据
    :param number: 第几条request.data
    :return: sourlist:sourcedita所有键值keys列表;sourcedict：sourcedata对应的键，值--值为list
    '''
    if number == 1:
        for d in data.keys():
            sourlist.append(d)
            sourcedict[d] = []
            sourcedict[d].append(str(data[d]))
    else:
        for d in data.keys():
            if d not in sourlist:
                sourlist.append(d)
                sourcedict[d] = []
                for s in range(number-1):
                    sourcedict[d].append("")
                sourcedict[d].append(data[d])
        for k in sourlist:
            try:
                sourcedict[k].append(str(data[k]))
            except KeyError:
                sourcedict[k].append("")
    return sourlist,sourcedict

    logging.debug("add_uncertain_data.data:{}".format(data))
    logging.debug("add_uncertain_data.data.type:{}".format(type(data)))
    logging.debug("number:{}".format(number))
    logging.debug("sourlist:{}".format(sourlist))
    logging.debug("sourcedict:{}".format(sourcedict))

def drop_empty(string):
    string = string.strip()
    return string.replace("\n","")
def sovedict(data,keys):
    '''
    :param data: 字典数据
    :param keys: 需要匹配的键以"a.b.c"格式传入
    :return: str
    '''
    d = keys.split(".")
    logging.debug("sovedict-keys:{}".format(d))
    return _getvaluebykey(data,d)

def _getvaluebykey(data,keys):
    '''
    :param data: 字典数据
    :param keys: 需要匹配的键以"a.b.c"格式传入
    :return: str
    '''
    try:
        if len(keys) > 1:
            return _getvaluebykey(data[keys[0]],keys[1:])
        else:
            return str(data[keys[0]])
    except KeyError:
        logging.warning("this item can't sove to dict:{}".format(data,keys))
        return ""

def getsearchindex(index, days=7,connect="-"):
    totalDays = []
    totalIndex = []
    today = datetime.utcnow()
    for i in range(0, days):
        totalDays.append((today - timedelta(i)).__format__('%Y-%m-%d'))

    for i in totalDays:
        totalIndex.append(index + connect + i)
    return totalIndex

def getbody(query,start = 0,size = 500,isFilter = True,filter = None,sort = None):
    body = {
        "size": size,  # 返回查询条数
        "from": start,  # 返回起始页
        "sort": {"T": {"order": "desc"}},  # 排序
        "_source": ["M", "T", "host.name"] # 返回指定字段
    }
    if sort is not None:
        body["sort"] = sort
    if isFilter is not True:
        del body["_source"]
    else:
        if filter is not None:
            if isinstance(filter,list):
                body["_source"] = filter
            else:
                print("body filter is {} but need list".format(type(filter)))
    if isinstance(query,dict):
        for a in query.keys():
            body[a] = query[a]
        return body
    else:
        print("getbody method args need dict type")

def addKeyAndValeToDict(target,exitstarget,value):
    if isinstance(target,dict):
        if exitstarget in target.keys():
            if isinstance(target[exitstarget],dict):
                target[exitstarget]=[target[exitstarget]]
                target[exitstarget].append(value)
            elif isinstance(target[exitstarget],list):
                target[exitstarget].append(value)
            else:
                return target
        else:
            target[exitstarget] = []
            target[exitstarget].append(value)
        return target
    else:
        print("无法将目标数据加入非字典")
        return target

def from_list_get_need_key_and_value(data,keys,notequal = ""):
    if isinstance(data,list):
        for s in range(len(data)):
            if keys[0] in data[s].keys():
                if len(keys) > 1:
                    i = from_list_get_need_key_and_value(data[s][keys[0]],keys[1:])
                    if i != notequal and i != None:
                        return i
                else:
                    if data[keys[0]] != notequal:
                        return data[keys[0]]
                        break

    if isinstance(data,dict):
        if keys[0] in data.keys():
            if len(keys) > 1:
                from_list_get_need_key_and_value(data[keys[0]],keys[1:])
            else:
                if data[keys[0]] != notequal:
                    return data[keys[0]]



class TempleteWindow(QFrame):
    def __init__(self):
        super(TempleteWindow, self).__init__()
        self.setGeometry(200,200,get_current_screen_desktop().width()-400,get_current_screen_desktop().height()-400)
        #设置背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        #设置窗口无边框
        self.setWindowFlags(Qt.FramelessWindowHint)
        #设置主窗体
        self.widget = QWidget(self)
        self.widget.setGeometry(0,0,self.width(),self.height())
        self.widget.setObjectName("mainwidget")
        self.set_mw_style()
        #设置title格式
        self.title = QLabel(self.widget)
        self.title.setGeometry(0, 0, self.widget.width(), 30)
        self.title.setObjectName("title")
        self.settitle_style()
        #设置主窗口样式
        self.contentWindow = QWidget(self.widget)
        self.contentWindow.setObjectName("content")
        self.setcontent_window_style()
        self.contentWindow.setGeometry(0, self.title.height(), self.widget.width(),
                                       self.widget.height() - self.title.height())
        #设置父类需要的子类属性和方法
        self.son_attr = None
        #设置标题栏
        self.titlepic = QPushButton(self.title)
        # self.titlepic.setDisabled(True)
        self.titlepic.setStyleSheet("QPushbuttom:pressed{border:1px solid white;}")
        # self.titlepic.height = self.title.height()
        self.title_tit = QLabel(self.title)
        self.close_btn = QPushButton(self.title)
        self.close_btn.clicked.connect(self.btn_close)
        self.normal_btn = QPushButton(self.title)
        self.normal_btn.clicked.connect(self.btn_normal)
        self.min_btn = QPushButton(self.title)
        self.min_btn.clicked.connect(self.btn_min)

        self.title_tit.setGeometry(25, 0, self.title.width()-125, 30)
        self.close_btn.setGeometry(self.title.width() - 35,0,30,30)
        self.normal_btn.setGeometry(self.title.width() - 65, 0, 30, 30)
        self.min_btn.setGeometry(self.title.width() - 95, 0, 30, 30)

        self.min_btn.setIcon(QIcon(PIC_BASE_DIR + "min.ico"))
        self.normal_btn.setIcon(QIcon(PIC_BASE_DIR + "max.ico"))
        self.close_btn.setIcon(QIcon(PIC_BASE_DIR + "close.ico"))
        self.setTitleWindow()
        self._initDrag()

    def set_son_attr(self,maps):
        '''
        :param maps: 该参数以键值对形式传递{"Module": "mainWindow", "class": "MainWindow", "method": "windowResize", "args": self})
        :return:
        '''
        self.son_attr = maps

    def btn_icon(self):
        pass

    def btn_min(self):
        self.showMinimized()

    def btn_normal(self):
        if self.isMaximized():
            self.showNormal()
            self.normal_btn.setIcon(QIcon(PIC_BASE_DIR + "max.ico"))
        else:
            self.showMaximized()
            self.normal_btn.setIcon(QIcon(PIC_BASE_DIR + "normal.ico"))
    def btn_close(self):
        self.close()

    def set_title(self,title):
        font = QFont("华文行楷",10)
        self.title_tit.setFont(font)
        # self.title_tit.setStyleSheet("QPushButton{border:None;background-color:None;text-align:left}")
        self.title_tit.setText(title)

    def mouseDoubleClickEvent(self,QMouseEvent):
        if QMouseEvent.pos() in self._top_rect:
            self.btn_normal()

    def setTitleWindow(self,pic = PIC_BASE_DIR + "kibana.png"):
        self.titlepic.setGeometry(2, 2, 25, 25)
        self.titlepic.setIcon(QIcon(pic))

    def settitle_style(self,color = 'rgb(199,250,204)'):
        style = '''QLabel#title{{border-top-left-radius:10px;border-top-right-radius:10px;background-color:{};}}
                                            QPushButton{{border-radius:5px;}}
                                            QPushButton:hover{{border:1px solid white;}}
                                            QPushButton:pressed{{border:1px solid;background-color:gray}}'''.format(color)
        self.title.setStyleSheet(style)
    def setcontent_window_style(self,color = 'rgb(199,237,204)'):
        self.contentWindow.setStyleSheet('''QWidget#content{{background-color:{};border-top-style:dotted;
                                            border-bottom-left-radius:10px;border-bottom-right-radius:10px;}}'''.format(color))

    def set_mw_style(self,border_radius = "10px",bc ="rgba(200,230,200,0.8)",style = "" ):
        if not style:
            self.QWidget_style = r'''
            QWidget#mainwidget{{border-radius:{};
                    background-color:{};
                    }}'''.format(border_radius,bc)
        else:
            self.QWidget_style = style
        self.widget.setStyleSheet(self.QWidget_style)
    def resizeEvent(self, QResizeEvent):
        # 自定义窗口调整大小事件
        # 改变窗口大小的三个坐标范围
        # self._right_rect = [QPoint(x, y) for x in range(self.width() - 5, self.width() + 5)
        #                     for y in range(self.widget.height() + 20, self.height() - 5)]
        # self._bottom_rect = [QPoint(x, y) for x in range(1, self.width() - 5)
        #                      for y in range(self.height() - 5, self.height() + 1)]
        # self._corner_rect = [QPoint(x, y) for x in range(self.width() - 5, self.width() + 1)
        #                      for y in range(self.height() - 5, self.height() + 1)]
        self._top_rect = [QPoint(x, y) for x in range(30,self.width()-60)
                             for y in range(30)]
        #标题窗口和内容窗口和主显示窗口大小调整
        self.widget.setGeometry(0, 0, self.width(), self.height())
        self.title.setGeometry(0, 0, self.widget.width(), 30)
        self.contentWindow.setGeometry(0, self.title.height(), self.widget.width(),self.widget.height() - self.title.height())
        self.title_tit.setGeometry(25, 0, self.title.width() - 125, 30)
        self.close_btn.setGeometry(self.title.width() - 35, 0, 30, 30)
        self.normal_btn.setGeometry(self.title.width() - 65, 0, 30, 30)
        self.min_btn.setGeometry(self.title.width() - 95, 0, 30, 30)
        #如果子类有需要resize方法，resizeEvent同时调用子类方法
        if self.son_attr:
            try:
                module = importlib.import_module(self.son_attr["Module"])
                cla = getattr(module,self.son_attr["class"])
                meth = getattr(cla,self.son_attr["method"])
                meth(self.son_attr["args"])
            except Exception as e:
               print(e)


    def _initDrag(self):
        # 设置鼠标跟踪判断扳机默认值
        self._move_drag = False

    def mousePressEvent(self, event):
        # 重写鼠标点击的事件
        if (event.button() == Qt.LeftButton) and (event.pos() in self._top_rect):
            # 鼠标左键点击标题栏区域
            self._move_drag = True
            self.move_DragPosition = event.globalPos() - self.pos()
            event.accept()

        else:
            self._move_drag = False
            # self._bottom_drag = False

    def mouseMoveEvent(self, QMouseEvent):
        if Qt.LeftButton and self._move_drag:
            # 标题栏拖放窗口位置
            self.move(QMouseEvent.globalPos() - self.move_DragPosition)
            QMouseEvent.accept()



    def mouseReleaseEvent(self, QMouseEvent):
        # 鼠标释放后，各扳机复位
        self._move_drag = False

    def showwindinw(self):
        self.show()

class JSONEncoder(json.JSONEncoder):
    """处理ObjectId,该类型无法转为json"""
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return datetime.strftime(o, '%Y-%m-%d %H:%M:%S')
        return json.JSONEncoder.default(self, o)

class Tablewidget(QTableWidget):
    def __init__(self,parent):
        super().__init__()
        self.setParent(parent)
        self.frontandnextFlag = []
        self.pat = re.compile(r"<font style='background-color:red;'>(.*?)</font>")
        self.searchbox = QFrame(self)
        self.searchbox.setGeometry(10,50,330,30)
        # self.searchbox.setFrameRect(QRect(10,10,10,10))
        self.searchbox.setStyleSheet("border-radius:2px;background-color:rgb(200,200,200)")
        self.searchbox.setHidden(True)

        self.searchtextbox = QLineEdit(self.searchbox)
        self.searchtextbox.setGeometry(0,0,210,30)
        self.searchtextbox.setStyleSheet("border:none")

        #文本显示框
        self.textwindow = QTextEdit(self)
        self.textwindow.setGeometry(0,0, self.width() - 100, self.height() - 100)
        self.textwindow.setVisible(False)
        self.textwindow_text = None
        #搜索窗口
        self.search = QPushButton("", self.searchbox)
        self.search.setIcon(QIcon("./pic/search.ico"))
        self.search.setGeometry(210, 0, 30, 30)
        self.search.setStyleSheet("border:none")
        self.search.clicked.connect(self.searchdata)

        self.front  =   QPushButton("",self.searchbox)
        self.front.setIcon(QIcon("./pic/front.ico"))
        self.front.setGeometry(240,0,30,30)
        self.front.setStyleSheet("border:none")
        self.front.clicked.connect(lambda: self.frontandnextpress(-1))

        self.next   =   QPushButton("", self.searchbox)
        self.next.setIcon(QIcon("./pic/next.ico"))
        self.next.setGeometry(270,0,30,30)
        self.next.setStyleSheet("border:none")
        self.next.clicked.connect(lambda: self.frontandnextpress(1))

        self.clo = QPushButton("", self.searchbox)
        self.clo.setIcon(QIcon("./pic/close.ico"))
        self.clo.setGeometry(300, 0, 30, 30)
        self.clo.setStyleSheet("border:none")
        self.clo.clicked.connect(self.searchboxclo)

        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        # 设置垂直方向滑块像素移动
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        # 设置水平方向滑块像素移动
        self.setEditTriggers(QAbstractItemView.NoEditTriggers | QAbstractItemView.DoubleClicked)
        # 设置表格不可编辑
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # 设置启用右键策略

    def showdata(self, data):
        self.setRowCount(len(data[0]) - 1)
        self.setColumnCount(len(data))
        for i in range(0, len(data)):  # 总列数,显示所有数据
            self.setHorizontalHeaderItem(i, QTableWidgetItem(data[i][0]))
            for j in range(1, len(data[0])):  # 总数据行数
                ss = QTableWidgetItem(data[i][j])
                self.setItem(j - 1, i, ss)
                ss.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # 设置所有单元格对齐方式

    def keyPressEvent(self, QkeyEvent):
        if QkeyEvent.key() == Qt.Key_F:
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.searchbox.show()
                self.searchbox.setHidden(False)
                self.searchtextbox.setFocus()
        elif QkeyEvent.key() == Qt.Key_Escape:
            if self.searchbox.isHidden():
                self.textwindow.setHidden(True)
            else:
                self.searchbox.setHidden(True)
                self.textwindow.setHidden(True)
        elif QkeyEvent.key() == Qt.Key_F2:
            self.textwindow.setGeometry(0,0, self.width() - 100, self.height() - 100)
            detail = JSONEncoder().encode(self.textwindow_text)
            detail = json.loads(detail)
            self.textwindow.setText(json.dumps(detail, indent=5, ensure_ascii=False))
            self.textwindow.setHidden(False)


    def searchdata(self):
        self.frontandnextFlag = []
        global  pressFlag
        pressFlag = -1
        findtext = ""
        # if self.searchtextbox.text() == "":
        #     return
        # else:
        try:
            findtext = self.searchtextbox.text().split()[0]
        except IndexError:
            findtext = "$@##$$@!!"  #如果为空，标记特殊寻找字符，找不到将Qlabel替换为字符串
        for a in range(self.rowCount()):
            for b in range(self.columnCount()):
                if isinstance(type(self.item(a,b)),type(None)) and isinstance(type(self.cellWidget(a,b)),type(None)):
                    pass
                else:

                    if isinstance(type(self.cellWidget(a,b)),type(QLabel)):
                        if "<font style" in self.cellWidget(a,b).text():
                            d = self.cancelCssFormat(self.cellWidget(a,b).text())
                            celltext = self.cellWidget(a,b).text().replace(
                                "<font style='background-color:red;'>{}</font>".format(d),
                                d)
                            if findtext in celltext:
                                self.cellWidget(a,b).setText(self.setStrkeyColor(celltext,findtext))
                                self.frontandnextFlag.append([a,b])
                            else:
                                self.removeCellWidget(a,b)
                                celltext = celltext.replace("<br>", "\n")
                                self.setItem(a,b,QTableWidgetItem(celltext))
                        else:
                            celltext = self.cellWidget(a,b).text()
                            celltext = celltext.replace("<br>", "\n")
                            self.removeCellWidget(a,b)
                            self.setItem(a,b,QTableWidgetItem(celltext))
                    elif isinstance(type(self.item(a, b)), type(QTableWidgetItem)):
                        if findtext in self.item(a,b).text():
                            celltext = self.item(a,b).text().replace("\n","<br>")
                            celltext = self.setStrkeyColor(celltext,findtext)
                            lab = QLabel(celltext,self)
                            self.setCellWidget(a,b,lab)
                            self.setItem(a,b,QTableWidgetItem(""))
                            self.frontandnextFlag.append([a, b])
                            # print(a,b,type(self.cellWidget(a,b)),type(self.item(a,b)),"\n",lab.text())
                        else:
                            pass
                    else:
                        pass

    def setStrkeyColor(self,strdata,key):
        needstr = strdata.replace(key,"<font style='background-color:red;'>{}</font>".format(key))
        return needstr

    def cancelCssFormat(self,strdata):
        return self.pat.search(strdata).group(1)

    def stecellbackcolor(self,a,b,color=QColor(200,200,200)):
        self.item(a,b).setBackground(QColor(color))

    def searchboxclo(self):
        self.searchtextbox.clear()
        self.searchbox.close()

    def frontandnextpress(self,k):
        global pressFlag
        pressFlag += k
        if pressFlag >= 0 and pressFlag < len(self.frontandnextFlag):
            self.setCurrentCell(self.frontandnextFlag[pressFlag][0],self.frontandnextFlag[pressFlag][1])
        else:
            pressFlag = -1


class GetElasticsearchData():
    def __new__(cls, body,index,es="http://elk.vesync.com:9200"):
        cls.body=body
        cls.index=index
        cls.es=es


        return super().__new__(cls)
    @classmethod
    def getalldata(cls):
        es = Elasticsearch(cls.es)
        try:
            responseResult = es.search(body=cls.body, index=cls.index, ignore_unavailable=True)
            return responseResult
        except Exception as elasticsearchErr:
            pass

class GetOpsData():
    def __new__(cls, userid):
        cls.userid=userid
        return super().__new__(cls)
    @classmethod
    def getdata(cls):
        url="http://ops.vesync.com:8000/api/getUserInfo?uid={}&envValue=prd".format(cls.userid)
        cookie={"csrftoken":"6xRludy3Ptn4p2Kxk775JAN8xFqKRS7SSwgsDZ1NX8a95qiYawbbVoj6IgrqjLfx", "sessionid":"gtq9q1iux068y61k20kdx8szre9010an"}
        header={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
        rsp=requests.get(url,cookies=cookie,headers=header).json()
        return rsp
class ShowMovieAndOther():
    def __init__(self,fa,usemethod,achieved,args=()):
        fa.showmovie = ShowMovie(fa.width(), fa.height(), fa)
        fa.showmovie.showMovie()
        fa.start = ThreadMethod(usemethod, args)
        fa.start.start()
        fa.start.acheived.connect(fa.showmovie.cloMovie)
        fa.start.acheived.connect(achieved)

class ShowMovie(QLabel):
    def __init__(self,width,height,parent):
        super(ShowMovie,self).__init__()
        self.setParent(parent)
        self.setGeometry(width/2 - 100, height / 2 - 100, 200, 200)
        self.movie = QMovie("./pic/loading.gif")
        self.movie.setScaledSize(self.size())
        self.setMovie(self.movie)
    def showMovie(self):
        self.show()
        self.movie.start()
    def cloMovie(self):
        self.movie.stop()
        self.close()


class ThreadMethod(QThread):
    acheived=pyqtSignal()
    def __init__(self,method,args):
        super(ThreadMethod,self).__init__()
        self.method=method
        self.args=args
        self.stopFlag=False

    def run(self,flag=0):
        if self.args==():
            self.method()
        else:
            self.method(arg for arg in self.args)
        self.acheived.emit()

'''
将字典键解析成a.b.c格式，或者a.b.c解析成对应字典的值
'''
class UsefulMethod():
    def __init__(self):
        pass
    '''
    提取字典的所有键值为a.b.c格式,返回iterable
    '''
    @classmethod
    def getMainkeyAndSonkey(cls, d, sk="", s=[]):
        print(type(d),d)
        for k, v in d.items():
            if type(v) is dict:
                if sk == "":
                    sk = k
                else:
                    sk = sk + "." + k
                ddd = UsefulMethod.getMainkeyAndSonkey(v, sk)
                for a in ddd:
                    yield a
                sk = sk.split(".")
                if len(sk) == 1:
                    sk = ""
                else:
                    sk = ".".join(sk[:-1])
                # 因yield使用中，该层字典遍历完成后保存的sk为当前的值，而不是调用函数进行赋值操作，所以需要对sk的值重新定义，切掉末尾的键值
            else:
                if sk == "":
                    yield k
                else:
                    yield (sk + "." + k)
    '''
    访问dictdata的["a","b","c"]元素
    '''
    @classmethod
    def parseindex(cls,dictdata,a):
        try:
            for s in a:
                if len(a) ==0:
                    pass
                elif len(a) == 1:
                    yield dictdata[a[0]]
                else:
                    dd=UsefulMethod.parseindex(dictdata[a[0]],a[1:])
                    for t in dd:
                        yield t
                        return
        except KeyError:
            # yield  None
            yield ""
        except TypeError:
            # yield None
            yield ""
    @classmethod
    def getsignaldictkey(cls,dictdata,keyvalue):
        value=""
        for x in dictdata[keyvalue]:
            value=x
        return value


class DictAndStrTransfer():
    indexlist = []
    globalvars = []
    # def __new__(cls, indexlist = [], globalvars = []):
    #     cls.indexlist  = indexlist
    #     cls.globalvars = globalvars
    #     return object.__new__(cls,cls.indexlist,cls.globalvars)

    @classmethod
    def transfer_to_index(cls, data, index=""):
        # logging.debug("transfer_to_index_data:{}".format(data))
        # print("index,data:{},{}".format(index,data))
        if isinstance(data, str):
            if data.startswith("{"):
                # print("into transfer:{}".format(index))
                data = cls.transfertodict(data)

        if isinstance(data, dict):
            for d, k in data.items():
                if index == "":
                    index = d
                else:
                    index = index + "." + d
                cls.transfer_to_index(k, index)
                index = index.split(".")
                if len(index) == 1:
                    index = ""
                else:
                    index = ".".join(index[:-1])
        elif isinstance(data,list):
            for s in data:
                cls.transfer_to_index(s,index)
        else:
            if index not in cls.indexlist:
                cls.indexlist.append(index)
        # logging.debug("\ntransfer_to_index_indexlist:{}".format(cls.indexlist))
    @classmethod
    def transfertodict(cls, data):
        try:
            data = eval(data)
            logging.debug("transfertodict-data:{}".format(data))
        except Exception as transformErr:
            if "NameError" in transformErr.__repr__():
                d = re.search(r"\'(.*?)\'", transformErr.__str__()).group(1)
                globals()[d] = d
                if d not in cls.globalvars:
                    cls.globalvars.append(d)
                return cls.transfertodict(data)
            else:
                raise transformErr
        return data

    @classmethod
    def transfer_index_to_indexlist(cls, index):
        return index.split(".")

    @classmethod
    def get_data_byindex(cls, data, indexlist):
        if len(indexlist) != 0:
            if isinstance(data, str):
                if data.startswith("{") or data.startswith("\'{") or data.startswith("\"{"):
                    data = cls.transfertodict(data)
                    logging.debug("get_data_byindex-data:{}".format(data))
                else:
                    pass
            if isinstance(data, dict):
                try:
                    return cls.get_data_byindex(data[indexlist[0]], indexlist[1:])
                except KeyError:
                    return ""
                except IndexError:
                    return str(data[indexlist[0]])
            else:
                pass
        if len(indexlist) == 0:
            return data
        else:
            return ""

    @classmethod
    def get_globalvars(cls):
        return cls.globalvars

    @classmethod
    def get_indexlist(cls):
        return cls.indexlist

    def clear_indexlist(self):
        cls.indexlist.clear()

    def clear_globalvars(self):
        cls.globalvars.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    s = TempleteWindow()
    s.set_title("测试查询")

    s.showwindinw()
    app.exec_()