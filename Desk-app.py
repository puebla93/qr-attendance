import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import sqlite3
import cv2
import zbar
import beep
import datetime
import socket
import json

# error_message = None
message_box = None
spin_box = None
scan_button = None
stop_button= None
subject_lineEdit = None
classtype_lineEdit = None
details_textEdit = None
userName_lineEdit = None
password_lineEdit = None
pending_uploaded_label = None
camera_image = None
camera_timer = None
capture = None
scanner = None
db = None
asist = []

def main():
    app = QApplication(sys.argv)

    global db
    db = sqlite3.connect('attendance.db')
    db.execute('''CREATE TABLE IF NOT EXISTS attendance
             (id integer, date timestamp, subject text, classtype text, name text, uploaded boolean, details text)''')

    global camera_timer
    camera_timer = QTimer()

    widget = QWidget()
    widget.setWindowTitle("Attendance")
    widget_izq = QWidget()
    widget_der = QWidget()

    horizontal_layout = QHBoxLayout()
    vertical_layout_izq = QVBoxLayout()
    vertical_layout_der = QVBoxLayout()
    
    widget.setLayout(horizontal_layout)
    widget_izq.setLayout(vertical_layout_izq)
    widget_der.setLayout(vertical_layout_der)

    # global dialogBox
    # dialogBox = QErrorMessage()
    global message_box
    message_box = QMessageBox()
    message_box.setWindowTitle("Error Message")

    global spin_box
    global scan_button
    global stop_button
    global userName_lineEdit
    global password_lineEdit
    global pending_uploaded_label
    spin_box_label = QLabel("Choose a camera index")
    spin_box = QSpinBox()
    scan_button = QPushButton("Scan")
    upload_button = QPushButton("Upload")
    stop_button = QPushButton("Stop")
    stop_button.setEnabled(False)
    userName_label = QLabel("User Name")
    userName_lineEdit = QLineEdit()
    password_label = QLabel("Password")
    password_lineEdit = QLineEdit()
    password_lineEdit.setEchoMode(2)
    pending_uploaded_label = QLabel("Missing " + str(pending_uploaded()) + " student(s) to upload")

    global camera_image
    global subject_lineEdit
    global classtype_lineEdit
    global details_textEdit
    camera_image = QLabel()
    pix_map = QPixmap("Image-Black.png")
    camera_image.setPixmap(pix_map)
    subject_label = QLabel("Subject")
    subject_lineEdit = QLineEdit()
    classtype_label = QLabel("Classtype")
    classtype_lineEdit = QLineEdit()
    details_Label = QLabel("Details")
    details_textEdit = QTextEdit()

    vertical_layout_izq.addWidget(spin_box_label)
    vertical_layout_izq.addWidget(spin_box)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(scan_button)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(stop_button)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(subject_label)
    vertical_layout_izq.addWidget(subject_lineEdit)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(classtype_label)
    vertical_layout_izq.addWidget(classtype_lineEdit)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(details_Label)
    vertical_layout_izq.addWidget(details_textEdit)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(userName_label)
    vertical_layout_izq.addWidget(userName_lineEdit)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(password_label)
    vertical_layout_izq.addWidget(password_lineEdit)
    vertical_layout_izq.addStretch()
    vertical_layout_izq.addWidget(upload_button)
    vertical_layout_izq.addWidget(pending_uploaded_label)
    
    vertical_layout_der.addWidget(camera_image)
    
    horizontal_layout.addWidget(widget_izq)
    horizontal_layout.addWidget(widget_der)

    scan_button.clicked.connect(start_scan)
    stop_button.clicked.connect(cancel_scan)
    upload_button.clicked.connect(upload)
    camera_timer.timeout.connect(procces_frame)

    widget.show()

    app.exec_()

class QRCode(object):
    """QRCode class"""
    def __init__(self, data, location):
        self.data = data
        self.location = list(location)

    def repr(self):
        return str(self.data)

class QRScanner(object):
    """Zbar qrcode scanner wrapper class"""
    def __init__(self, width, height):
        self.scanner = zbar.ImageScanner()
        self.scanner.parse_config('enable')
        self.width = width
        self.height = height

    def get_qrcodes(self, image):
        zbar_img = self.cv2_to_zbar_image(image)
        self.scanner.scan(zbar_img)
        result=[]
        for symbol in zbar_img:
            if str(symbol.type)!=str(zbar.Symbol.QRCODE): continue
            fixed_data = symbol.data.decode("utf8").encode("shift_jis").decode("utf8")
            result.append(QRCode(fixed_data,symbol.location))
        del(zbar_img)
        return result

    def cv2_to_zbar_image(self, cv2_image):
        return zbar.Image(self.width, self.height, 'Y800',cv2_image.tostring())

def valid_qrcode(qrcode_data):

    qrcode_data = qrcode_data.split("\n")
    if len(qrcode_data) != 5 : return False

    #N: Nombre
    test = qrcode_data[0].split(":")
    if test[0] != "N" or len(test[1]) == 0: return False

    #A\: Apellidos
    test = qrcode_data[1].split(":")
    if test[0] != "A" or len(test[1]) == 0: return False

    #CI\: 12345678901
    test = qrcode_data[2].split(":")
    if test[0] != "CI" or len(test[1].strip()) != 11: return False

    #FV\: AA0000000
    test = qrcode_data[3].split(":")
    if test[0] != "FV" or len(test[1].strip()) != 9: return False

    return True

def get_student_info(qrcode_data):
    # sacar la info del qrcode
    qrcode_data = qrcode_data.split("\n")

    return {
                "ID": qrcode_data[2][-12:].strip(),
                "Name": qrcode_data[0][2:].strip() + " " + qrcode_data[1][2:].strip(),
            }

def upload():
    user_name = userName_lineEdit.text()
    password = password_lineEdit.text()

    HOST = 'localhost'
    PORT = 80

    my_socked = socket.socket()
    # my_socked.connect((HOST, PORT))

    cur = db.execute("SELECT * FROM attendance WHERE uploaded = 'False'")
    for line in cur.fetchall():
        print(line)
        # my_socked.send()

    my_socked.close()

def procces_frame():
    image = None
    global capture
    if capture is None:
        capture = cv2.VideoCapture(spin_box.value())
        _ , image = capture.read()
        if image is None:
            cancel_scan()
            # error_message.showMessage("Invalid camera index. Use -c option to choose a correct camera on your system.")
            # error_message.show()
            message_box.setText("Invalid camera index.")
            message_box.show()
            return
        h, w, c = image.shape
        global  scanner
        scanner = QRScanner(w,h)
    if image is None:
        _ , image = capture.read()
    
    #Poner en un metodo showImage(image)
    h, w, c = image.shape
    cv2.cvtColor(image, cv2.COLOR_BGR2RGB, image)
    qimage = QImage(image, w, h, c * w, QImage.Format_RGB888)
    pix_map = QPixmap.fromImage(qimage)
    camera_image.setPixmap(pix_map)

    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    result = scanner.get_qrcodes(gray_image)

    if len(result) == 0:
        return

    for qr in result:
        if not valid_qrcode(qr.data):
            continue
        student = get_student_info(qr.data)

        scanned = False
        #COMPROBAR SI EL ESTUDIANTE YA HA SIDO INSERTADO EN LA BASE DE DATOS
        for s in asist:
           if s == student["ID"]: scanned= True

        if not scanned:
            asist.append(student["ID"])
            date = datetime.datetime.now()
            subject = subject_lineEdit.text()
            classtype = classtype_lineEdit.text()
            details =  details_textEdit.toPlainText()
            db.execute('''INSERT INTO attendance VALUES (?, ?, ?, ?, ?, 'False', ?)''', 
                        [student["ID"], date, subject, classtype, student["Name"], details])
            # Save (commit) the changes
            db.commit()
            beep.beep()

def start_scan():
    stop_button.setEnabled(True)
    scan_button.setEnabled(False)
    camera_timer.start(50)

def cancel_scan():
    stop_button.setEnabled(False)
    scan_button.setEnabled(True)
    camera_timer.stop()
    global capture
    capture.release()
    capture = None
    pix_map = QPixmap("Image-Black.png")
    camera_image.setPixmap(pix_map)
    global pending_uploaded_label
    pending_uploaded_label.setText("Missing " + str(pending_uploaded()) + " student(s) to upload")

def pending_uploaded():
    cur = db.execute("SELECT COUNT(*) FROM attendance WHERE uploaded = 'False'")
    count = cur.fetchone()
    return count[0]

if __name__ == '__main__':
    main()