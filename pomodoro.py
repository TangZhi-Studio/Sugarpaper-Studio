import os
import sys
import json
import time
import math
import random
from datetime import date

from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QFont, QPixmap, QIcon
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QSpinBox, QLineEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QMessageBox,
    QSizePolicy, QFrame
)

APP_NAME = "Pomodoro_Tool"
APP_VERSION = "1.1.0"


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


STATS_FILE = os.path.join(app_dir(), "pomodoro_stats.json")
SETTINGS_FILE = os.path.join(app_dir(), "pomodoro_settings.json")

DEFAULT_SETTINGS = {
    "work_sec": 1500,
    "short_sec": 300,
    "long_sec": 900,
    "rounds": 4,
    "auto_next": True,
}


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(default, dict):
                d = dict(default)
                d.update(data)
                return d
            return data
    except Exception:
        return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


BG = "#1e1f26"
CARD = "#262833"
TEXT = "#e8e8ef"
SUB = "#8d90a0"
GREEN = "#57c785"
RED = "#e8705f"
BLUE = "#5b9cf0"

STYLE = """
QWidget {
    background: %s;
    color: %s;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
}
QFrame#card {
    background: %s;
    border-radius: 12px;
}
QLabel#modeLabel {
    font-size: 15px;
    color: %s;
}
QLabel#statLabel {
    font-size: 13px;
    color: %s;
}
QPushButton {
    background: #343747;
    color: %s;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-size: 13px;
}
QPushButton:hover { background: #43475c; }
QPushButton:pressed { background: #2d3040; }
QPushButton#primary {
    background: %s;
    color: #17251c;
    font-weight: bold;
}
QPushButton#primary:hover { background: #6ad495; }
QPushButton#danger {
    background: %s;
    color: #2a1513;
    font-weight: bold;
}
QPushButton#danger:hover { background: #f08374; }
QLineEdit, QSpinBox {
    background: #1a1b22;
    color: %s;
    border: 1px solid #343747;
    border-radius: 8px;
    padding: 6px 8px;
    selection-background-color: %s;
}
QLineEdit:focus, QSpinBox:focus { border-color: %s; }
QCheckBox { color: %s; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 4px;
    border: 1px solid #4a4e63;
    background: #1a1b22;
}
QCheckBox::indicator:checked {
    background: %s;
    border-color: %s;
}
""" % (BG, TEXT, CARD, SUB, SUB, TEXT, GREEN, RED, TEXT, GREEN, BLUE, SUB, GREEN, GREEN)


def play_sound():
    try:
        if sys.platform.startswith("win"):
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        else:
            QApplication.beep()
    except Exception:
        try:
            QApplication.beep()
        except Exception:
            pass


class RingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 1.0
        self.mode = "work"
        self.time_text = "25:00"
        self.setMinimumSize(240, 240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_state(self, progress, mode, time_text):
        self.progress = max(0.0, min(1.0, progress))
        self.mode = mode
        self.time_text = time_text
        self.update()

    def mode_color(self):
        return GREEN if self.mode == "work" else BLUE

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height())
        rect = QRectF(
            (self.width() - side) / 2 + 12,
            (self.height() - side) / 2 + 12,
            side - 24,
            side - 24,
        )

        pen = painter.pen()
        pen.setColor(QColor("#343747"))
        pen.setWidth(10)
        painter.setPen(pen)
        painter.drawArc(rect, 90 * 16, -360 * 16)

        pen = painter.pen()
        pen.setColor(QColor(self.mode_color()))
        pen.setWidth(10)
        painter.setPen(pen)
        painter.drawArc(rect, 90 * 16, int(-360 * 16 * self.progress))

        painter.setPen(QColor(TEXT))
        font = QFont("Microsoft YaHei", int(side / 8))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.time_text)


class EggOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.hide()
        self.count = 10
        self.t = 0.0
        self.life = 4.0
        self.particles = []
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.step)

    def start(self, count):
        self.count = count
        self.t = 0.0
        self.particles = []
        colors = ["#e8705f", "#f2b95c", "#57c785", "#5b9cf0", "#c98bf0", "#f07fb0"]
        for i in range(52):
            self.particles.append({
                "x": random.uniform(-0.05, 1.05),
                "y": random.uniform(-0.9, -0.05),
                "vy": random.uniform(0.22, 0.55),
                "vx": random.uniform(-0.06, 0.06),
                "size": random.uniform(13, 26),
                "rot": random.uniform(0, 360),
                "vrot": random.uniform(-200, 200),
                "kind": 0 if i % 3 else 1,
                "color": random.choice(colors),
            })
        self.timer.start()

    def step(self):
        self.t += 0.016
        for p in self.particles:
            p["y"] += p["vy"] * 0.016
            p["x"] += p["vx"] * 0.016
            p["rot"] += p["vrot"] * 0.016
            if p["y"] > 1.18:
                p["y"] = -0.16
                p["x"] = random.uniform(-0.05, 1.05)
        self.update()
        if self.t >= self.life:
            self.timer.stop()
            self.hide()

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        fade = 1.0
        if self.t > self.life - 0.7:
            fade = max(0.0, (self.life - self.t) / 0.7)
        qp.setOpacity(fade)
        qp.fillRect(self.rect(), QColor(20, 21, 26, 120))

        for p in self.particles:
            x = p["x"] * self.width()
            y = p["y"] * self.height()
            size = p["size"]
            qp.save()
            qp.translate(QPointF(x, y))
            qp.rotate(p["rot"])
            qp.setPen(Qt.NoPen)
            qp.setBrush(QColor(p["color"]))
            if p["kind"] == 0:
                qp.drawEllipse(QRectF(-size / 2, -size / 2, size, size))
                qp.setBrush(QColor("#57c785"))
                qp.drawEllipse(QRectF(-size / 5, -size / 1.6, size / 2.5, size / 3.2))
            else:
                qp.drawRect(QRectF(-size / 6, -size / 1.5, size / 3, size / 0.9))
            qp.restore()

        if self.t < 0.35:
            scale = 0.7 + 0.3 * (self.t / 0.35)
        else:
            scale = 1.0

        font = QFont("Microsoft YaHei", int(30 * scale))
        font.setBold(True)
        qp.setFont(font)
        qp.setPen(QColor(255, 255, 255))
        rect = self.rect()
        rect.setTop(rect.center().y() - 70)
        qp.drawText(rect, Qt.AlignHCenter | Qt.AlignTop, "第 {} 个番茄达成！".format(self.count))

        font = QFont("Microsoft YaHei", 14)
        qp.setFont(font)
        qp.setPen(QColor(200, 202, 214))
        rect2 = self.rect()
        rect2.setTop(rect2.center().y() + 8)
        qp.drawText(rect2, Qt.AlignHCenter | Qt.AlignTop, "奖励自己好好休息一下")


class PomodoroWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_json(SETTINGS_FILE, dict(DEFAULT_SETTINGS))
        self.stats = self.load_stats()

        self.mode = "work"
        self.running = False
        self.remaining = float(self.settings["work_sec"])
        self.duration = self.remaining
        self.end_time = None
        self.finished_pomodoros = 0
        self.current_task = ""
        self.pending_next_mode = "short"

        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.tick)

        self.init_ui()
        self.switch_mode("work", force=True)
        self.refresh_stats_label()

    def load_stats(self):
        today = date.today().isoformat()
        data = load_json(STATS_FILE, {"date": today, "pomodoros": 0, "focus_seconds": 0, "tasks": []})
        if data.get("date") != today:
            data = {"date": today, "pomodoros": 0, "focus_seconds": 0, "tasks": []}
            save_json(STATS_FILE, data)
        return data

    def save_stats(self):
        save_json(STATS_FILE, self.stats)

    def focus_text(self):
        sec = int(self.stats.get("focus_seconds", 0))
        m, s = divmod(sec, 60)
        if m > 0 and s > 0:
            return "{} 分 {} 秒".format(m, s)
        if m > 0:
            return "{} 分钟".format(m)
        return "{} 秒".format(s)

    def refresh_stats_label(self):
        self.stat_label.setText("今日：番茄 {} 个 · 专注 {}".format(
            self.stats.get("pomodoros", 0), self.focus_text()
        ))

    def init_ui(self):
        self.setWindowTitle("番茄钟 v{}".format(APP_VERSION))
        self.setMinimumSize(470, 800)
        self.setStyleSheet(STYLE)
        self.setWindowIcon(self.make_icon())

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(12)

        title = QLabel("番茄钟")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        root.addWidget(title)

        self.stat_label = QLabel()
        self.stat_label.setObjectName("statLabel")
        root.addWidget(self.stat_label)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(10)

        self.mode_label = QLabel("专注中")
        self.mode_label.setObjectName("modeLabel")
        self.mode_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.mode_label)

        self.ring = RingWidget()
        card_layout.addWidget(self.ring, 1)

        self.task_label = QLabel("当前任务：未设置")
        self.task_label.setObjectName("statLabel")
        self.task_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.task_label)

        root.addWidget(card, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.start_btn = QPushButton("开始")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self.toggle_start)
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_phase)
        self.skip_btn = QPushButton("跳过")
        self.skip_btn.clicked.connect(lambda: self.finish_phase(counted=False))
        btn_row.addWidget(self.start_btn, 2)
        btn_row.addWidget(self.reset_btn, 1)
        btn_row.addWidget(self.skip_btn, 1)
        root.addLayout(btn_row)

        task_row = QHBoxLayout()
        task_row.setSpacing(8)
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("写点当前要做的事（可选）")
        self.task_input.returnPressed.connect(self.set_task)
        task_btn = QPushButton("设定")
        task_btn.clicked.connect(self.set_task)
        task_row.addWidget(self.task_input, 1)
        task_row.addWidget(task_btn)
        root.addLayout(task_row)

        settings_card = QFrame()
        settings_card.setObjectName("card")
        grid = QGridLayout(settings_card)
        grid.setContentsMargins(16, 12, 16, 12)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        grid.addWidget(self.make_time_row("专注", "work_sec", 180), 0, 0, 1, 2)
        grid.addWidget(self.make_time_row("短休息", "short_sec", 60), 1, 0, 1, 2)
        grid.addWidget(self.make_time_row("长休息", "long_sec", 60), 2, 0, 1, 2)

        rounds_row = QWidget()
        rh = QHBoxLayout(rounds_row)
        rh.setContentsMargins(0, 0, 0, 0)
        rh.setSpacing(6)
        rl = QLabel("几轮后长休")
        rl.setStyleSheet("color:#8d90a0;")
        rl.setFixedWidth(72)
        self.rounds_spin = QSpinBox()
        self.rounds_spin.setRange(2, 12)
        self.rounds_spin.setSuffix(" 个")
        self.rounds_spin.setValue(int(self.settings["rounds"]))
        self.rounds_spin.valueChanged.connect(self.on_rounds_changed)
        rh.addWidget(rl)
        rh.addWidget(self.rounds_spin)
        rh.addStretch(1)
        grid.addWidget(rounds_row, 3, 0, 1, 2)

        self.auto_check = QCheckBox("完成一轮后自动开始下一阶段")
        self.auto_check.setChecked(bool(self.settings.get("auto_next", True)))
        self.auto_check.stateChanged.connect(self.on_auto_changed)
        grid.addWidget(self.auto_check, 4, 0, 1, 2)

        root.addWidget(settings_card)

        tip = QLabel("快捷键：空格 开始/暂停 · R 重置 · S 跳过")
        tip.setStyleSheet("color:#6f7387; font-size:12px;")
        tip.setAlignment(Qt.AlignCenter)
        root.addWidget(tip)

        self.egg = EggOverlay(self)

    def make_time_row(self, label_text, key, max_min):
        row = QWidget()
        rh = QHBoxLayout(row)
        rh.setContentsMargins(0, 0, 0, 0)
        rh.setSpacing(6)

        lb = QLabel(label_text)
        lb.setStyleSheet("color:#8d90a0;")
        lb.setFixedWidth(72)

        total = max(1, int(self.settings[key]))
        spin_m = QSpinBox()
        spin_m.setRange(0, max_min)
        spin_m.setSuffix(" 分")
        spin_m.setValue(total // 60)

        spin_s = QSpinBox()
        spin_s.setRange(0, 59)
        spin_s.setSuffix(" 秒")
        spin_s.setValue(total % 60)

        def changed():
            sec = spin_m.value() * 60 + spin_s.value()
            if sec <= 0:
                sec = 1
            self.on_time_changed(key, sec)

        spin_m.valueChanged.connect(lambda v: changed())
        spin_s.valueChanged.connect(lambda v: changed())

        rh.addWidget(lb)
        rh.addWidget(spin_m)
        rh.addWidget(spin_s)
        rh.addStretch(1)
        return row

    def make_icon(self):
        pm = QPixmap(64, 64)
        pm.fill(QColor(BG))
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(RED))
        painter.drawEllipse(QRectF(14, 18, 36, 34))
        painter.setBrush(QColor(GREEN))
        painter.drawEllipse(QRectF(26, 8, 10, 14))
        painter.end()
        return QIcon(pm)

    def on_time_changed(self, key, seconds):
        self.settings[key] = int(seconds)
        save_json(SETTINGS_FILE, self.settings)
        if not self.running:
            self.switch_mode(self.mode, force=True)

    def on_rounds_changed(self, value):
        self.settings["rounds"] = int(value)
        save_json(SETTINGS_FILE, self.settings)

    def on_auto_changed(self, state):
        self.settings["auto_next"] = bool(state)
        save_json(SETTINGS_FILE, self.settings)

    def set_task(self):
        text = self.task_input.text().strip()
        self.current_task = text
        self.task_label.setText("当前任务：" + (text if text else "未设置"))
        if text and text not in self.stats.get("tasks", []):
            self.stats.setdefault("tasks", []).append(text)
            self.save_stats()

    def mode_duration(self, mode):
        if mode == "work":
            return max(1, int(self.settings["work_sec"]))
        if mode == "short":
            return max(1, int(self.settings["short_sec"]))
        return max(1, int(self.settings["long_sec"]))

    def mode_name(self, mode):
        return {"work": "专注中", "short": "短休息", "long": "长休息"}[mode]

    def switch_mode(self, mode, force=False):
        self.mode = mode
        self.duration = float(self.mode_duration(mode))
        self.remaining = self.duration
        self.end_time = None
        if force:
            self.running = False
            self.timer.stop()
            self.start_btn.setText("开始")
            self.set_primary_style()
        self.mode_label.setText(self.mode_name(mode))
        self.update_display()

    def set_primary_style(self):
        self.start_btn.setObjectName("primary")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

    def set_danger_style(self):
        self.start_btn.setObjectName("danger")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)

    def toggle_start(self):
        if self.running:
            self.pause()
        else:
            self.start()

    def start(self):
        if self.remaining <= 0:
            self.remaining = self.duration
        self.end_time = time.monotonic() + self.remaining
        self.running = True
        self.timer.start()
        self.start_btn.setText("暂停")
        self.set_danger_style()

    def pause(self):
        if self.end_time is not None:
            self.remaining = max(0.0, self.end_time - time.monotonic())
        self.running = False
        self.timer.stop()
        self.start_btn.setText("继续")
        self.set_primary_style()
        self.update_display()

    def reset_phase(self):
        self.running = False
        self.timer.stop()
        self.duration = float(self.mode_duration(self.mode))
        self.remaining = self.duration
        self.start_btn.setText("开始")
        self.set_primary_style()
        self.update_display()

    def tick(self):
        if not self.running or self.end_time is None:
            return
        left = self.end_time - time.monotonic()
        if left <= 0:
            self.remaining = 0.0
            self.update_display()
            self.finish_phase(counted=True)
        else:
            self.remaining = left
            self.update_display()

    def update_display(self):
        seconds = int(math.ceil(max(0.0, self.remaining)))
        mm, ss = divmod(seconds, 60)
        if mm >= 60:
            hh, mm2 = divmod(mm, 60)
            text = "{}:{:02d}:{:02d}".format(hh, mm2, ss)
        else:
            text = "{:02d}:{:02d}".format(mm, ss)
        self.ring.set_state(
            self.remaining / self.duration if self.duration > 0 else 0,
            self.mode,
            text,
        )

    def finish_phase(self, counted=True):
        self.running = False
        self.timer.stop()
        self.start_btn.setText("开始")
        self.set_primary_style()

        finished_mode = self.mode
        egged = False

        if finished_mode == "work":
            self.finished_pomodoros += 1
            if counted:
                self.stats["pomodoros"] = self.stats.get("pomodoros", 0) + 1
                self.stats["focus_seconds"] = self.stats.get("focus_seconds", 0) + int(self.settings["work_sec"])
                self.save_stats()
                self.refresh_stats_label()

            rounds = int(self.settings["rounds"])
            next_mode = "long" if self.finished_pomodoros % rounds == 0 else "short"

            if counted:
                play_sound()
                total = self.stats.get("pomodoros", 0)
                if total > 0 and total % 10 == 0:
                    egged = True
                    self.pending_next_mode = next_mode
                    self.show_egg(total)
                else:
                    self.show_finish_msg(next_mode)
        else:
            next_mode = "work"
            if counted:
                play_sound()
                QMessageBox.information(self, "休息结束", "休息结束，开始下一个番茄吧！")

        self.switch_mode(next_mode, force=True)

        if egged:
            QTimer.singleShot(4300, self.after_egg)
        elif self.settings.get("auto_next", True):
            QTimer.singleShot(300, self.start)

    def show_finish_msg(self, next_mode):
        QMessageBox.information(
            self, "番茄完成",
            "完成第 {} 个番茄！\n接下来：{}".format(
                self.finished_pomodoros,
                "长休息" if next_mode == "long" else "短休息",
            )
        )

    def after_egg(self):
        if self.settings.get("auto_next", True):
            self.start()

    def show_egg(self, count):
        self.egg.setGeometry(self.rect())
        self.egg.start(count)
        self.egg.show()
        self.egg.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "egg"):
            self.egg.setGeometry(self.rect())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.toggle_start()
        elif event.key() == Qt.Key_R:
            self.reset_phase()
        elif event.key() == Qt.Key_S:
            self.finish_phase(counted=False)
        else:
            super().keyPressEvent(event)


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    window = PomodoroWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
