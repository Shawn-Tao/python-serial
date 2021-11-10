import sys
import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from Ui_uitrolley_controller import Ui_Form
import sys
import time

class Pyqt5_Serial(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(Pyqt5_Serial, self).__init__()
        self.setupUi(self)
        self.init()
        self.setWindowTitle("天宝小车交互软件")
        self.ser = serial.Serial()
        self.port_check()
        self.receive_data = ''
        self.send_data = ''
        self.trolley_num = '01'
        self.filepth = "log.txt"
        self.incval = ''

    def init(self):
        # 串口检测按钮
        self.s1__box_1.clicked.connect(self.port_check)

        # 串口信息显示
        self.s1__box_2.currentTextChanged.connect(self.port_imf)

        # 打开串口按钮
        self.open_button.clicked.connect(self.port_open)

        # 关闭串口按钮
        self.close_button.clicked.connect(self.port_close)

        # 定时器接收数据
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.data_receive)

        # 清除发送窗口
        self.s3__clear_button.clicked.connect(self.send_data_clear)

        # 清除接收窗口
        self.s2__clear_button.clicked.connect(self.receive_data_clear)

        # 小车初始化与测量
        self.button_init.clicked.connect(self.initialize)
        self.button_measure.clicked.connect(self.measure)
        self.button_inc.clicked.connect(self.calib_inc)

    # 串口检测
    def port_check(self):
        # 检测所有存在的串口，将信息存储在字典中
        self.Com_Dict = {}
        port_list = list(serial.tools.list_ports.comports())
        self.s1__box_2.clear()
        for port in port_list:
            self.Com_Dict["%s" % port[0]] = "%s" % port[1]
            self.s1__box_2.addItem(port[0])
        if len(self.Com_Dict) == 0:
            self.state_label.setText(" 无串口")

    # 串口信息
    def port_imf(self):
        # 显示选定的串口的详细信息
        imf_s = self.s1__box_2.currentText()
        if imf_s != "":
            self.state_label.setText(self.Com_Dict[self.s1__box_2.currentText()])

    # 打开串口
    def port_open(self):
        self.ser.port = self.s1__box_2.currentText()
        self.ser.baudrate = int(self.s1__box_3.currentText())
        self.ser.bytesize = int(self.s1__box_4.currentText())
        self.ser.stopbits = int(self.s1__box_6.currentText())
        self.ser.parity = self.s1__box_5.currentText()

        try:
            self.ser.open()
        except:
            QMessageBox.critical(self, "Port Error", "此串口不能被打开！")
            return None

        # 打开串口接收定时器，周期为2ms
        self.timer.start(2)

        if self.ser.isOpen():
            self.open_button.setEnabled(False)
            self.close_button.setEnabled(True)

    # 关闭串口
    def port_close(self):
        self.timer.stop()
        try:
            self.ser.close()
        except:
            pass
        self.open_button.setEnabled(True)
        self.close_button.setEnabled(False)

    # 接收数据
    def data_receive(self):
        try:
            num = self.ser.inWaiting()
        except:
            self.port_close()
            return None
        if num > 0:
            data = self.ser.read_until(b'\x0d')
            out_s = ''
            for i in range(0, len(data)):
                out_s = out_s + '{:02X}'.format(data[i]) + ' '
            self.text_receive_hex.insertPlainText(out_s+"\r\n")

            self.text_receive_ascall.insertPlainText(data.decode('iso-8859-1'))

            with open(self.filepth,"a", encoding="iso-8859-1") as fileout:
                fileout.write(data.decode('iso-8859-1'))
            fileout.close()

            textCursor = self.text_receive_hex.textCursor()
            textCursor.movePosition(textCursor.End)
            self.text_receive_hex.setTextCursor(textCursor)
            return data.decode('iso-8859-1')

        else:
            return None

    # 清除显示
    def send_data_clear(self):
        self.s3__send_text.setText("")

    def receive_data_clear(self):
        self.text_receive_ascall.setText("")
        self.text_receive_hex.setText("")

    def send_and_wait(self, command):
        if(command == "#MASTER"):
            print('master')
            if(self.ser.isOpen()):
                try:
                    self.timer.stop()
                    self.ser.write((command+ '\r').encode('iso-8859-1'))
                    self.s3__send_text.insertPlainText(command+"\r\n")
                except:
                    QMessageBox.critical(self, 'Wrong Operation', "文件写出错误")
                    return None

                with open(self.filepth,"a", encoding="iso-8859-1") as fileout:
                    fileout.write(command+"\r")
                fileout.close()
                time.sleep(0.01)
                count = 0;

                while(count < 20000):
                    recv = self.data_receive()
                    if(recv == None):
                        count += 1
                        time.sleep(0.01)
                    else:
                        self.trolley_num = recv[1:-1]
                        print(recv)
                        break

                self.timer.start()
                return True
            else:
                QMessageBox.critical(self, 'Wrong Operation', '请先打开串口')
                time.sleep(0.01)
                return False

        elif(command == "#01INC"):
            print('inc')
            if(self.ser.isOpen()):
                try:
                    self.timer.stop()
                    self.ser.write((command+ '\r').encode('iso-8859-1'))
                    self.s3__send_text.insertPlainText(command+"\r\n")
                except:
                    QMessageBox.critical(self, 'Wrong Operation', "文件写出错误")
                    return None

                with open(self.filepth,"a", encoding="iso-8859-1") as fileout:
                    fileout.write(command+"\r")
                fileout.close()
                time.sleep(0.01)
                count = 0;

                while(count < 20):
                    recv = self.data_receive()
                    if(recv == None):
                        count += 1
                        time.sleep(0.01)
                    else:
                        self.incval = recv
                        print(recv)
                        break

                self.timer.start()
                return True
            else:
                QMessageBox.critical(self, 'Wrong Operation', '请先打开串口')
                time.sleep(0.01)
                return False

        elif(command == '#01SETINC'+"\""+"\""):
            if(self.incval != ''):
                print('setinc')
                command == '#01SETINC'+"\""+self.incval+"\""
                if(self.ser.isOpen()):
                    try:
                        self.ser.write((command+ '\r').encode('iso-8859-1'))
                        self.s3__send_text.insertPlainText(command+"\r\n")
                    except:
                        QMessageBox.critical(self, 'Wrong Operation', "文件写出错误")
                        return None

                    with open(self.filepth,"a", encoding="iso-8859-1") as fileout:
                        fileout.write(command+"\r")
                    fileout.close()
                    time.sleep(0.01)
                    return True

                else:
                    QMessageBox.critical(self, 'Wrong Operation', '请先打开串口')
                    time.sleep(0.01)
                    return False
            else:
                QMessageBox.critical(self, 'Wrong Operation', '请先进行初始化')
                time.sleep(0.01)
                return False
            
        else:
            if(self.ser.isOpen()):
                try:
                    self.ser.write((command+ '\r').encode('iso-8859-1'))
                    self.s3__send_text.insertPlainText(command+"\r\n")
                except:
                    QMessageBox.critical(self, 'Wrong Operation', "文件写出错误")
                    return None

                with open(self.filepth,"a", encoding="iso-8859-1") as fileout:
                    fileout.write(command+"\r")
                fileout.close()
                time.sleep(0.01)
                return True
            else:
                QMessageBox.critical(self, 'Wrong Operation', '请先打开串口')
                time.sleep(0.01)
                return False
        

    def initialize(self):
        if(self.ser.isOpen()):
            if(self.checkBox_1.isChecked()):
                self.send_and_wait('#MASTER')
            if(self.checkBox_2.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'SN')
            if(self.checkBox_3.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'TROLLEY')
            if(self.checkBox_4.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'INC')
            if(self.checkBox_5.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'CONT0')
            if(self.checkBox_6.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'FW')
            if(self.checkBox_7.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'CONF')
            if(self.checkBox_8.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'ADC')
            if(self.checkBox_9.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'DMI')
            if(self.checkBox_10.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'INCTAB')
            if(self.checkBox_11.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'GAUGE')
            if(self.checkBox_12.isChecked()): 
                self.send_and_wait('#'+self.trolley_num+'FR')
            if(self.checkBox_13.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'PROFILER')
            if(self.checkBox_14.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'SCANNER')
            if(self.checkBox_15.isChecked()):
                self.send_and_wait('#'+self.trolley_num+'MK')
        else:
            QMessageBox.critical(self, 'Wrong Operation', '请先打开串口')

        textCursor = self.s3__send_text.textCursor()
        textCursor.movePosition(textCursor.End)
        self.s3__send_text.setTextCursor(textCursor)

    def measure(self):
        self.send_and_wait('#'+self.trolley_num+'MK')
        
        textCursor = self.s3__send_text.textCursor()
        textCursor.movePosition(textCursor.End)
        self.s3__send_text.setTextCursor(textCursor)

    def calib_inc(self):
        inc_str = self.lineEdit_inc.text()
        self.send_and_wait('#'+self.trolley_num+'SETINC'+"\""+inc_str+"\"")
        
        textCursor = self.s3__send_text.textCursor()
        textCursor.movePosition(textCursor.End)
        self.s3__send_text.setTextCursor(textCursor)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myshow = Pyqt5_Serial()
    myshow.show()
    sys.exit(app.exec_())
