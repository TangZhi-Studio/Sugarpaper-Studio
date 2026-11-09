import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QSpinBox, QGroupBox, QMessageBox)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

class PomodoroWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("番茄钟工具")
        self.resize(420,320)
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.total_seconds = 25 * 60
        self.left_seconds = self.total_seconds
        self.running = False

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        setting_group = QGroupBox("时间设置(分钟)")
        setting_layout = QHBoxLayout(setting_group)

        setting_layout.addWidget(QLabel("工作:"))
        self.spin_work = QSpinBox()
        self.spin_work.setRange(1,120)
        self.spin_work.setValue(25)
        setting_layout.addWidget(self.spin_work)

        setting_layout.addWidget(QLabel("休息:"))
        self.spin_rest = QSpinBox()
        self.spin_rest.setRange(1,60)
        self.spin_rest.setValue(5)
        setting_layout.addWidget(self.spin_rest)

        layout.addWidget(setting_group)

        self.label_time = QLabel("25:00")
        self.label_time.setFont(QFont("Consolas",42,QFont.Bold))
        self.label_time.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_time)

        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("开始")
        self.btn_pause = QPushButton("暂停")
        self.btn_reset = QPushButton("重置")
        self.btn_work = QPushButton("切换工作模式")
        self.btn_rest = QPushButton("切换休息模式")

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_pause)
        btn_layout.addWidget(self.btn_reset)
        layout.addLayout(btn_layout)

        btn_layout2 = QHBoxLayout()
        btn_layout2.addWidget(self.btn_work)
        btn_layout2.addWidget(self.btn_rest)
        layout.addLayout(btn_layout2)

        self.btn_start.clicked.connect(self.start_timer)
        self.btn_pause.clicked.connect(self.pause_timer)
        self.btn_reset.clicked.connect(self.reset_timer)
        self.btn_work.clicked.connect(self.set_work_mode)
        self.btn_rest.clicked.connect(self.set_rest_mode)

        self.setStyleSheet("""
        QMainWindow{background:#2b2b2b;}
        QWidget{color:#eeeeee;background:#2b2b2b;}
        QGroupBox{border:1px solid #555555;}
        QPushButton{background:#404040;border:1px solid #606060;padding:6px;}
        QPushButton:hover{background:#505050;}
        QSpinBox{background:#353535;border:1px solid #606060;}
        """)

    def format_time(self, sec):
        m = sec // 60
        s = sec % 60
        return f"{m:02d}:{s:02d}"

    def refresh_display(self):
        self.label_time.setText(self.format_time(self.left_seconds))

    def start_timer(self):
        if not self.running:
            self.running = True
            self.timer.start(1000)

    def pause_timer(self):
        self.running = False
        self.timer.stop()

    def reset_timer(self):
        self.pause_timer()
        self.left_seconds = self.total_seconds
        self.refresh_display()

    def set_work_mode(self):
        self.pause_timer()
        val = self.spin_work.value()
        self.total_seconds = val * 60
        self.left_seconds = self.total_seconds
        self.refresh_display()

    def set_rest_mode(self):
        self.pause_timer()
        val = self.spin_rest.value()
        self.total_seconds = val * 60
        self.left_seconds = self.total_seconds
        self.refresh_display()

    def tick(self):
        self.left_seconds -= 1
        self.refresh_display()
        if self.left_seconds <= 0:
            self.pause_timer()
            QMessageBox.information(self,"提示","时间到！")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PomodoroWindow()
    win.show()
    sys.exit(app.exec_())
