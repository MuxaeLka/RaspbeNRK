"""
NRK Manager — менеджер Raspberry Pi через WireGuard
Управление устройствами NRK с мониторингом доступности и веб-интерфейсом.
"""

import os
import sys
import json
import time
import socket
import webbrowser
import threading
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QHeaderView, QDialog, QFormLayout, QDialogButtonBox, QTextEdit,
    QSplitter, QMessageBox, QMenu, QAbstractItemView, QStatusBar,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSortFilterProxyModel,
    QItemSelectionModel, QSize
)
from PyQt6.QtGui import (
    QColor, QFont, QIcon, QPalette, QBrush, QAction,
    QLinearGradient, QPainter, QPixmap
)

# ─── Константы ────────────────────────────────────────────────────────────────

CONFIG_FILE = Path("config.json")
WEB_PORT = 8080       # порт по умолчанию для Raspberry Pi
MIKROTIK_PORT = 80    # порт по умолчанию для MikroTik
PING_TIMEOUT = 2          # секунд на попытку TCP-connect
CHECK_INTERVAL_MS = 5000  # интервал автопроверки, мс
APP_VERSION = "1.0.0"

DEFAULT_DEVICES = [
    {"name": "NRK-1", "ip": "10.60.93.50", "port": 8080, "device_type": "raspberry"},
    {"name": "NRK-2", "ip": "10.60.93.51", "port": 8080, "device_type": "raspberry"},
    {"name": "NRK-3", "ip": "10.60.93.52", "port": 8080, "device_type": "raspberry"},
    {"name": "NRK-4", "ip": "10.60.93.53", "port": 8080, "device_type": "raspberry"},
    {"name": "NRK-5", "ip": "10.60.93.54", "port": 8080, "device_type": "raspberry"},
    {"name": "NRK-6", "ip": "10.60.93.55", "port": 8080, "device_type": "raspberry"},
    {"name": "NRK-7", "ip": "10.60.93.56", "port": 8080, "device_type": "raspberry"},
]

# ─── Цветовая палитра ──────────────────────────────────────────────────────────

PALETTE = {
    "bg_deep":     "#0d1117",   # фон окна
    "bg_panel":    "#161b22",   # фон панелей
    "bg_table":    "#0d1117",   # фон таблицы
    "bg_row_alt":  "#111820",   # чётные строки
    "bg_selected": "#1f3a5f",   # выделенная строка
    "accent":      "#388bfd",   # синий акцент (WireGuard-blue)
    "accent_hover":"#58a6ff",
    "online":      "#3fb950",   # зелёный
    "offline":     "#f85149",   # красный
    "warn":        "#d29922",   # жёлтый
    "text_main":   "#e6edf3",
    "text_dim":    "#8b949e",
    "text_accent": "#58a6ff",
    "border":      "#30363d",
    "btn_bg":      "#21262d",
    "btn_hover":   "#30363d",
    "btn_primary": "#1f6feb",
    "btn_primary_h":"#388bfd",
    "log_bg":      "#0a0e14",
    "log_border":  "#21262d",
}

# ─── Таблица стилей ────────────────────────────────────────────────────────────

QSS = f"""
QMainWindow, QWidget {{
    background-color: {PALETTE['bg_deep']};
    color: {PALETTE['text_main']};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}}

QTableWidget {{
    background-color: {PALETTE['bg_table']};
    gridline-color: {PALETTE['border']};
    border: 1px solid {PALETTE['border']};
    border-radius: 6px;
    selection-background-color: {PALETTE['bg_selected']};
    selection-color: {PALETTE['text_main']};
    outline: none;
}}

QTableWidget::item {{
    padding: 6px 10px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: {PALETTE['bg_selected']};
    color: {PALETTE['text_main']};
}}

QHeaderView::section {{
    background-color: {PALETTE['bg_panel']};
    color: {PALETTE['text_dim']};
    border: none;
    border-bottom: 1px solid {PALETTE['border']};
    border-right: 1px solid {PALETTE['border']};
    padding: 8px 10px;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

QHeaderView::section:hover {{
    background-color: {PALETTE['btn_hover']};
    color: {PALETTE['text_main']};
}}

QHeaderView::section:last {{
    border-right: none;
}}

QPushButton {{
    background-color: {PALETTE['btn_bg']};
    color: {PALETTE['text_main']};
    border: 1px solid {PALETTE['border']};
    border-radius: 6px;
    padding: 7px 14px;
    font-size: 13px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {PALETTE['btn_hover']};
    border-color: {PALETTE['text_dim']};
}}

QPushButton:pressed {{
    background-color: {PALETTE['bg_deep']};
}}

QPushButton#primary {{
    background-color: {PALETTE['btn_primary']};
    color: #ffffff;
    border-color: {PALETTE['btn_primary']};
    font-weight: 600;
}}

QPushButton#primary:hover {{
    background-color: {PALETTE['btn_primary_h']};
    border-color: {PALETTE['btn_primary_h']};
}}

QPushButton#danger {{
    background-color: transparent;
    color: {PALETTE['offline']};
    border-color: {PALETTE['offline']};
}}

QPushButton#danger:hover {{
    background-color: rgba(248, 81, 73, 0.15);
}}

QLineEdit {{
    background-color: {PALETTE['bg_panel']};
    color: {PALETTE['text_main']};
    border: 1px solid {PALETTE['border']};
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 13px;
    selection-background-color: {PALETTE['accent']};
}}

QLineEdit:focus {{
    border-color: {PALETTE['accent']};
    background-color: {PALETTE['bg_deep']};
}}

QTextEdit {{
    background-color: {PALETTE['log_bg']};
    color: {PALETTE['text_dim']};
    border: 1px solid {PALETTE['log_border']};
    border-radius: 6px;
    font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
    font-size: 11px;
    padding: 6px;
}}

QLabel {{
    color: {PALETTE['text_main']};
    background: transparent;
}}

QLabel#heading {{
    font-size: 18px;
    font-weight: 700;
    color: {PALETTE['text_main']};
    letter-spacing: -0.3px;
}}

QLabel#subheading {{
    font-size: 12px;
    color: {PALETTE['text_dim']};
}}

QLabel#section_title {{
    font-size: 11px;
    font-weight: 600;
    color: {PALETTE['text_dim']};
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}

QSplitter::handle {{
    background-color: {PALETTE['border']};
    width: 1px;
    height: 1px;
}}

QScrollBar:vertical {{
    background: {PALETTE['bg_panel']};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {PALETTE['border']};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background: {PALETTE['text_dim']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {PALETTE['bg_panel']};
    height: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: {PALETTE['border']};
    border-radius: 4px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {PALETTE['text_dim']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QStatusBar {{
    background-color: {PALETTE['bg_panel']};
    color: {PALETTE['text_dim']};
    border-top: 1px solid {PALETTE['border']};
    font-size: 11px;
    padding: 2px 6px;
}}

QDialog {{
    background-color: {PALETTE['bg_panel']};
}}

QDialogButtonBox QPushButton {{
    min-width: 80px;
}}

QMenu {{
    background-color: {PALETTE['bg_panel']};
    color: {PALETTE['text_main']};
    border: 1px solid {PALETTE['border']};
    border-radius: 6px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 16px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {PALETTE['bg_selected']};
}}

QFrame#separator {{
    background-color: {PALETTE['border']};
    max-height: 1px;
    min-height: 1px;
}}
"""

# ─── Вспомогательная функция: иконка приложения ───────────────────────────────

def _icon_fallback() -> QIcon:
    """Программная иконка — буква N в круге. Используется если .ico не найден."""
    px = QPixmap(64, 64)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor(PALETTE["bg_panel"])))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, 60, 60)
    from PyQt6.QtGui import QPen
    pen = QPen(QColor(PALETTE["accent"]))
    pen.setWidth(3)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(3, 3, 58, 58)
    font = QFont("Segoe UI", 28, QFont.Weight.Bold)
    p.setFont(font)
    p.setPen(QColor(PALETTE["text_main"]))
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "N")
    p.end()
    return QIcon(px)


def make_app_icon() -> QIcon:
    """
    Загружает иконку: сначала из _MEIPASS (EXE), потом resources/ рядом с файлом,
    в случае неудачи рисует программно.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))

    candidates = []
    if meipass:
        candidates.append(os.path.join(meipass, "icon.ico"))
    candidates.append(os.path.join(exe_dir, "resources", "icon.ico"))
    candidates.append(os.path.join(os.getcwd(), "resources", "icon.ico"))

    for path in candidates:
        if os.path.isfile(path):
            icon = QIcon(path)
            if not icon.isNull():
                return icon

    return _icon_fallback()

# ─── Модель устройства ─────────────────────────────────────────────────────────

# Типы устройств
DEVICE_TYPES = {
    "raspberry": {"label": "Raspberry Pi", "color": "#e67e22", "default_port": 8080},
    "mikrotik":  {"label": "MikroTik",     "color": "#388bfd", "default_port": 80},
}


class Device:
    """Одно устройство с состоянием мониторинга. Поддерживает Raspberry Pi и MikroTik."""

    def __init__(self, name: str, ip: str, port: int = WEB_PORT,
                 device_type: str = "raspberry"):
        self.name = name
        self.ip = ip
        self.port = port
        self.device_type = device_type  # "raspberry" | "mikrotik"
        self.online: bool | None = None   # None = ещё не проверяли
        self.ping_ms: float | None = None
        self.last_seen: datetime | None = None

    def web_url(self) -> str:
        """URL для открытия в браузере / Winbox."""
        if self.device_type == "mikrotik":
            return f"winbox://{self.ip}"
        return f"http://{self.ip}:{self.port}"

    def type_label(self) -> str:
        return DEVICE_TYPES.get(self.device_type, {}).get("label", self.device_type)

    def type_color(self) -> str:
        return DEVICE_TYPES.get(self.device_type, {}).get("color", PALETTE["text_dim"])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ip": self.ip,
            "port": self.port,
            "device_type": self.device_type,
        }

    @staticmethod
    def from_dict(d: dict) -> "Device":
        return Device(
            name=d["name"],
            ip=d["ip"],
            port=d.get("port", WEB_PORT),
            device_type=d.get("device_type", "raspberry"),
        )

# ─── Поток проверки одного устройства ─────────────────────────────────────────

class PingWorker(QThread):
    """
    Выполняет TCP-connect на порт 8080 чтобы определить доступность.
    Используем TCP вместо ICMP — не требует прав администратора.
    """
    result = pyqtSignal(str, bool, float)  # ip, online, ping_ms

    def __init__(self, ip: str, port: int, timeout: float = PING_TIMEOUT):
        super().__init__()
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self._stop_flag = False

    def run(self):
        if self._stop_flag:
            return
        t0 = time.monotonic()
        try:
            with socket.create_connection((self.ip, self.port), timeout=self.timeout):
                pass
            elapsed = (time.monotonic() - t0) * 1000  # в мс
            self.result.emit(self.ip, True, round(elapsed, 1))
        except (OSError, socket.timeout, ConnectionRefusedError):
            elapsed = (time.monotonic() - t0) * 1000
            self.result.emit(self.ip, False, round(elapsed, 1))

    def stop(self):
        self._stop_flag = True

# ─── Диалог добавления/редактирования устройства ──────────────────────────────

class DeviceDialog(QDialog):
    def __init__(self, parent=None, device: Device | None = None):
        super().__init__(parent)
        self.setWindowTitle("Устройство" if device is None else "Редактировать устройство")
        self.setModal(True)
        self.setMinimumWidth(360)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Добавить устройство" if device is None else "Изменить устройство")
        title.setObjectName("heading")
        title.setStyleSheet(f"font-size:15px; font-weight:700; color:{PALETTE['text_main']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("NRK-8 / Router-1")

        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("10.60.93.57")

        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("8080")

        # Выбор типа устройства — два радио-подобных кнопки
        from PyQt6.QtWidgets import QComboBox
        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet(
            f"QComboBox {{ background:{PALETTE['bg_panel']}; color:{PALETTE['text_main']};"
            f"border:1px solid {PALETTE['border']}; border-radius:6px; padding:6px 10px;}}"
            f"QComboBox::drop-down {{ border:none; }}"
            f"QComboBox QAbstractItemView {{ background:{PALETTE['bg_panel']};"
            f"color:{PALETTE['text_main']}; selection-background-color:{PALETTE['bg_selected']};}}"
        )
        self.type_combo.addItem("Raspberry Pi", "raspberry")
        self.type_combo.addItem("MikroTik",     "mikrotik")
        # При смене типа — подставляем дефолтный порт
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)

        if device:
            self.name_edit.setText(device.name)
            self.ip_edit.setText(device.ip)
            self.port_edit.setText(str(device.port))
            idx = self.type_combo.findData(device.device_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        else:
            self.port_edit.setText("8080")

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"color:{PALETTE['text_dim']};")
            return l

        form.addRow(lbl("Название:"),  self.name_edit)
        form.addRow(lbl("IP-адрес:"),  self.ip_edit)
        form.addRow(lbl("Порт:"),      self.port_edit)
        form.addRow(lbl("Тип:"),       self.type_combo)
        layout.addLayout(form)

        # Подсказка под формой
        self.hint_lbl = QLabel()
        self.hint_lbl.setStyleSheet(f"color:{PALETTE['text_dim']}; font-size:11px;")
        self.hint_lbl.setWordWrap(True)
        layout.addWidget(self.hint_lbl)
        self._update_hint()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setObjectName("primary")
        layout.addWidget(buttons)

    def _on_type_changed(self, _idx: int):
        """При смене типа подставляем дефолтный порт если поле не редактировалось."""
        dtype = self.type_combo.currentData()
        default_port = DEVICE_TYPES.get(dtype, {}).get("default_port", 80)
        # Подставляем дефолт только если порт стандартный для другого типа
        current = self.port_edit.text().strip()
        known_defaults = {str(v["default_port"]) for v in DEVICE_TYPES.values()}
        if not current or current in known_defaults:
            self.port_edit.setText(str(default_port))
        self._update_hint()

    def _update_hint(self):
        dtype = self.type_combo.currentData()
        if dtype == "mikrotik":
            self.hint_lbl.setText(
                "Двойной клик открывает winbox://IP  •  "
                "Проверка: TCP-connect на указанный порт"
            )
        else:
            self.hint_lbl.setText(
                "Двойной клик открывает http://IP:PORT  •  "
                "Проверка: TCP-connect на указанный порт"
            )

    def _on_accept(self):
        name = self.name_edit.text().strip()
        ip   = self.ip_edit.text().strip()
        port = self.port_edit.text().strip()
        if not name or not ip or not port:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля.")
            return
        parts = ip.split(".")
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            QMessageBox.warning(self, "Ошибка", "Некорректный IP-адрес.")
            return
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            QMessageBox.warning(self, "Ошибка", "Порт должен быть числом от 1 до 65535.")
            return
        self.accept()

    def get_values(self) -> tuple[str, str, int, str]:
        return (
            self.name_edit.text().strip(),
            self.ip_edit.text().strip(),
            int(self.port_edit.text().strip()),
            self.type_combo.currentData(),
        )

# ─── Виджет заголовка ─────────────────────────────────────────────────────────

class HeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 12)
        layout.setSpacing(2)

        row = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(make_app_icon().pixmap(36, 36))
        row.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        t = QLabel("NRK Manager")
        t.setObjectName("heading")
        t.setStyleSheet(f"font-size:17px; font-weight:700; color:{PALETTE['text_main']};")
        sub = QLabel("Менеджер Raspberry Pi через WireGuard")
        sub.setObjectName("subheading")
        sub.setStyleSheet(f"font-size:11px; color:{PALETTE['text_dim']};")
        title_col.addWidget(t)
        title_col.addWidget(sub)

        row.addLayout(title_col)
        row.addStretch()

        self.status_lbl = QLabel("● Ожидание проверки")
        self.status_lbl.setStyleSheet(f"color:{PALETTE['text_dim']}; font-size:12px;")
        row.addWidget(self.status_lbl)

        layout.addLayout(row)
        self.setStyleSheet(f"background-color:{PALETTE['bg_panel']}; border-bottom:1px solid {PALETTE['border']};")

    def set_status(self, online: int, total: int):
        color = PALETTE["online"] if online == total else (
            PALETTE["warn"] if online > 0 else PALETTE["offline"]
        )
        self.status_lbl.setText(f"● {online}/{total} онлайн")
        self.status_lbl.setStyleSheet(f"color:{color}; font-size:12px; font-weight:600;")

# ─── Главное окно ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"NRK Manager v{APP_VERSION}")
        self.setMinimumSize(900, 620)
        self.resize(1100, 700)
        self.setWindowIcon(make_app_icon())

        # Устройства и воркеры
        self.devices: list[Device] = []
        self._workers: dict[str, PingWorker] = {}   # ip -> worker
        self._lock = threading.Lock()               # для безопасного доступа к workers

        # Загрузка конфига
        self._load_config()

        # Построение UI
        self._build_ui()
        self.setStyleSheet(QSS)

        # Первичное заполнение таблицы
        self._populate_table()

        # Таймер автопроверки
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_all)
        self._timer.start(CHECK_INTERVAL_MS)

        # Сразу запускаем проверку при старте
        QTimer.singleShot(300, self._check_all)

        self._log("Приложение запущено.")
        self._log(f"Загружено устройств: {len(self.devices)}")

    # ── Загрузка/сохранение конфига ───────────────────────────────────────────

    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                self.devices = [Device.from_dict(d) for d in data.get("devices", [])]
                return
            except Exception as e:
                print(f"[config] Ошибка чтения: {e}")
        # Файл отсутствует или повреждён — используем дефолт
        self.devices = [Device.from_dict(d) for d in DEFAULT_DEVICES]
        self._save_config()

    def _save_config(self):
        try:
            data = {"devices": [d.to_dict() for d in self.devices]}
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"[ОШИБКА] Сохранение конфига: {e}", error=True)

    # ── Построение интерфейса ─────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Заголовок
        self.header = HeaderWidget()
        root.addWidget(self.header)

        # Сплиттер: таблица + лог
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(4)
        root.addWidget(splitter)

        # Верхняя часть: тулбар + таблица
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(12, 12, 12, 8)
        top_layout.setSpacing(10)

        # Тулбар
        toolbar = self._build_toolbar()
        top_layout.addLayout(toolbar)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Название", "IP-адрес", "Тип", "Статус", "Отклик (мс)", "Последняя проверка"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_double_click)
        self.table.setStyleSheet(
            f"QTableWidget {{alternate-background-color: {PALETTE['bg_row_alt']};}}"
        )
        top_layout.addWidget(self.table)
        splitter.addWidget(top_widget)

        # Нижняя часть: лог
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(12, 4, 12, 10)
        log_layout.setSpacing(6)

        log_header = QHBoxLayout()
        log_title = QLabel("ЖУРНАЛ СОБЫТИЙ")
        log_title.setObjectName("section_title")
        log_title.setStyleSheet(
            f"font-size:10px; font-weight:600; color:{PALETTE['text_dim']}; letter-spacing:0.8px;"
        )
        log_header.addWidget(log_title)
        log_header.addStretch()
        clear_btn = QPushButton("Очистить")
        clear_btn.setFixedHeight(24)
        clear_btn.setStyleSheet(
            f"font-size:11px; padding:2px 10px; color:{PALETTE['text_dim']};"
            f"border-color:{PALETTE['border']};"
        )
        clear_btn.clicked.connect(lambda: self.log_view.clear())
        log_header.addWidget(clear_btn)
        log_layout.addLayout(log_header)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(180)
        self.log_view.setMinimumHeight(80)
        log_layout.addWidget(self.log_view)
        splitter.addWidget(log_widget)

        splitter.setSizes([460, 160])

        # Статусбар
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Готово")

    def _build_toolbar(self) -> QHBoxLayout:
        tb = QHBoxLayout()
        tb.setSpacing(8)

        # Поиск
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍  Поиск по имени или IP...")
        self.search_edit.setFixedHeight(32)
        self.search_edit.textChanged.connect(self._apply_filter)
        tb.addWidget(self.search_edit, stretch=1)

        tb.addSpacing(8)

        # Кнопки действий
        def btn(text, obj_name=None, tooltip=""):
            b = QPushButton(text)
            b.setFixedHeight(32)
            if obj_name:
                b.setObjectName(obj_name)
            if tooltip:
                b.setToolTip(tooltip)
            return b

        self.btn_open = btn("Открыть", "primary", "Открыть веб-интерфейс выбранного устройства")
        self.btn_open.clicked.connect(self._open_selected)
        tb.addWidget(self.btn_open)

        self.btn_open_all = btn("Открыть все", tooltip="Открыть веб-интерфейсы всех онлайн-устройств")
        self.btn_open_all.clicked.connect(self._open_all)
        tb.addWidget(self.btn_open_all)

        self.btn_refresh = btn("⟳  Обновить", tooltip="Немедленно проверить все устройства")
        self.btn_refresh.clicked.connect(self._check_all)
        tb.addWidget(self.btn_refresh)

        # Разделитель
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color:{PALETTE['border']};")
        tb.addWidget(sep)

        self.btn_add = btn("+ Добавить", tooltip="Добавить новое устройство")
        self.btn_add.clicked.connect(self._add_device)
        tb.addWidget(self.btn_add)

        self.btn_edit = btn("Изменить", tooltip="Редактировать выбранное устройство")
        self.btn_edit.clicked.connect(self._edit_device)
        tb.addWidget(self.btn_edit)

        self.btn_del = btn("Удалить", "danger", "Удалить выбранное устройство")
        self.btn_del.clicked.connect(self._delete_device)
        tb.addWidget(self.btn_del)

        return tb

    # ── Заполнение таблицы ────────────────────────────────────────────────────

    def _populate_table(self):
        """Перестроить таблицу из списка self.devices с учётом фильтра."""
        query = self.search_edit.text().strip().lower() if hasattr(self, "search_edit") else ""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        visible = [d for d in self.devices if
                   not query or query in d.name.lower() or query in d.ip.lower()]

        self.table.setRowCount(len(visible))
        for row, device in enumerate(visible):
            self._set_row(row, device)

        self.table.setSortingEnabled(True)
        self._update_header_status()

    def _set_row(self, row: int, device: Device):
        """Заполнить одну строку таблицы данными устройства."""
        # Храним IP в UserRole нулевой ячейки для быстрого поиска
        name_item = QTableWidgetItem(device.name)
        name_item.setData(Qt.ItemDataRole.UserRole, device.ip)
        name_item.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))
        self.table.setItem(row, 0, name_item)

        ip_item = QTableWidgetItem(device.ip)
        ip_item.setForeground(QBrush(QColor(PALETTE["text_dim"])))
        ip_item.setFont(QFont("Consolas", 12))
        self.table.setItem(row, 1, ip_item)

        # Тип устройства (col 2)
        type_item = QTableWidgetItem(device.type_label())
        type_item.setForeground(QBrush(QColor(device.type_color())))
        type_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, type_item)

        # Статус (col 3+)
        self._update_status_cells(row, device)

        self.table.setRowHeight(row, 40)

    def _update_status_cells(self, row: int, device: Device):
        """Обновить ячейки Статус / Отклик / Время в указанной строке.
        Колонки: 0=Название, 1=IP, 2=Тип, 3=Статус, 4=Отклик, 5=Время"""
        # Статус (col 3)
        if device.online is None:
            status_text = "⏳  Проверка..."
            status_color = PALETTE["text_dim"]
        elif device.online:
            status_text = "●  Онлайн"
            status_color = PALETTE["online"]
        else:
            status_text = "●  Офлайн"
            status_color = PALETTE["offline"]

        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(QBrush(QColor(status_color)))
        status_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        self.table.setItem(row, 3, status_item)

        # Отклик (col 4)
        if device.ping_ms is not None:
            ping_text = f"{device.ping_ms}"
            ping_color = (
                PALETTE["online"] if device.ping_ms < 100 else
                PALETTE["warn"] if device.ping_ms < 500 else
                PALETTE["offline"]
            )
        else:
            ping_text = "—"
            ping_color = PALETTE["text_dim"]
        ping_item = QTableWidgetItem(ping_text)
        ping_item.setForeground(QBrush(QColor(ping_color)))
        ping_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 4, ping_item)

        # Последняя проверка (col 5)
        if device.last_seen:
            ts = device.last_seen.strftime("%H:%M:%S")
        else:
            ts = "—"
        ts_item = QTableWidgetItem(ts)
        ts_item.setForeground(QBrush(QColor(PALETTE["text_dim"])))
        ts_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 5, ts_item)

    # ── Поиск ────────────────────────────────────────────────────────────────

    def _apply_filter(self, _text: str = ""):
        self._populate_table()

    # ── Проверка устройств ────────────────────────────────────────────────────

    def _check_all(self):
        """Запустить проверку всех устройств в параллельных потоках."""
        self.btn_refresh.setEnabled(False)
        QTimer.singleShot(1500, lambda: self.btn_refresh.setEnabled(True))

        for device in self.devices:
            self._check_device(device)

    def _check_device(self, device: Device):
        """Создать и запустить PingWorker для одного устройства."""
        ip = device.ip
        with self._lock:
            # Если уже работает — не дублируем
            if ip in self._workers and self._workers[ip].isRunning():
                return
            worker = PingWorker(ip, device.port)
            worker.result.connect(self._on_ping_result)
            # Удаляем воркер из словаря после завершения потока
            worker.finished.connect(lambda ip=ip: self._cleanup_worker(ip))
            self._workers[ip] = worker
            worker.start()

    def _cleanup_worker(self, ip: str):
        with self._lock:
            self._workers.pop(ip, None)

    def _on_ping_result(self, ip: str, online: bool, ping_ms: float):
        """
        Слот вызывается из GUI-потока (сигнал из QThread доставляется через очередь).
        Обновляем модель и перерисовываем строку в таблице.
        """
        # Ищем устройство
        device = next((d for d in self.devices if d.ip == ip), None)
        if device is None:
            return

        changed = device.online != online
        device.online = online
        device.ping_ms = ping_ms if online else None
        if online:
            device.last_seen = datetime.now()

        if changed:
            state = "онлайн" if online else "офлайн"
            self._log(f"{device.name} ({ip}) → {state}  [{ping_ms} мс]",
                      error=not online)

        # Обновляем строку в таблице (ищем по UserRole)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == ip:
                self._update_status_cells(row, device)
                break

        self._update_header_status()

    def _update_header_status(self):
        online_count = sum(1 for d in self.devices if d.online is True)
        self.header.set_status(online_count, len(self.devices))
        ts = datetime.now().strftime("%H:%M:%S")
        self.statusbar.showMessage(
            f"Онлайн: {online_count}/{len(self.devices)}  |  Обновлено: {ts}"
        )

    # ── Открытие браузера ─────────────────────────────────────────────────────

    def _get_selected_device(self) -> Device | None:
        rows = self.table.selectedItems()
        if not rows:
            return None
        row = self.table.currentRow()
        item = self.table.item(row, 0)
        if not item:
            return None
        ip = item.data(Qt.ItemDataRole.UserRole)
        return next((d for d in self.devices if d.ip == ip), None)

    def _open_selected(self):
        device = self._get_selected_device()
        if not device:
            QMessageBox.information(self, "Нет выбора", "Выберите устройство в таблице.")
            return
        self._open_device(device)

    def _open_device(self, device: Device):
        url = device.web_url()
        self._log(f"Открываем браузер: {url}")
        webbrowser.open(url)

    def _open_all(self):
        """Открыть все онлайн-устройства (или все, если нет онлайн)."""
        targets = [d for d in self.devices if d.online is True] or self.devices
        if not targets:
            return
        for device in targets:
            self._open_device(device)

    def _on_double_click(self, index):
        device = self._get_selected_device()
        if device:
            self._open_device(device)

    # ── Контекстное меню ──────────────────────────────────────────────────────

    def _show_context_menu(self, pos):
        device = self._get_selected_device()
        if not device:
            return

        menu = QMenu(self)
        act_open = QAction(f"Открыть {device.name}", self)
        act_open.triggered.connect(lambda: self._open_device(device))
        menu.addAction(act_open)

        act_check = QAction("Проверить сейчас", self)
        act_check.triggered.connect(lambda: self._check_device(device))
        menu.addAction(act_check)

        menu.addSeparator()

        act_edit = QAction("Редактировать...", self)
        act_edit.triggered.connect(self._edit_device)
        menu.addAction(act_edit)

        act_del = QAction("Удалить", self)
        act_del.triggered.connect(self._delete_device)
        menu.addAction(act_del)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    # ── CRUD устройств ────────────────────────────────────────────────────────

    def _add_device(self):
        dlg = DeviceDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, ip, port, dtype = dlg.get_values()
            if any(d.ip == ip for d in self.devices):
                QMessageBox.warning(self, "Дубликат", f"Устройство с IP {ip} уже существует.")
                return
            device = Device(name, ip, port, dtype)
            self.devices.append(device)
            self._save_config()
            self._populate_table()
            self._log(f"Добавлено устройство: {name} ({ip}:{port}) [{dtype}]")
            self._check_device(device)

    def _edit_device(self):
        device = self._get_selected_device()
        if not device:
            QMessageBox.information(self, "Нет выбора", "Выберите устройство в таблице.")
            return
        dlg = DeviceDialog(self, device)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            old_ip = device.ip
            new_name, new_ip, new_port, new_type = dlg.get_values()
            if new_ip != old_ip and any(d.ip == new_ip for d in self.devices):
                QMessageBox.warning(self, "Дубликат", f"Устройство с IP {new_ip} уже существует.")
                return
            device.name = new_name
            device.ip = new_ip
            device.port = new_port
            device.device_type = new_type
            device.online = None
            device.ping_ms = None
            self._save_config()
            self._populate_table()
            self._log(f"Изменено: {new_name} ({old_ip} → {new_ip}:{new_port}) [{new_type}]")
            self._check_device(device)

    def _delete_device(self):
        device = self._get_selected_device()
        if not device:
            QMessageBox.information(self, "Нет выбора", "Выберите устройство в таблице.")
            return
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить устройство {device.name} ({device.ip})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.devices.remove(device)
            self._save_config()
            self._populate_table()
            self._log(f"Удалено устройство: {device.name} ({device.ip})")

    # ── Журнал событий ────────────────────────────────────────────────────────

    def _log(self, message: str, error: bool = False):
        ts = datetime.now().strftime("%H:%M:%S")
        if error:
            html = f'<span style="color:{PALETTE["text_dim"]};">[{ts}]</span> <span style="color:{PALETTE["offline"]};">{message}</span>'
        else:
            html = f'<span style="color:{PALETTE["text_dim"]};">[{ts}]</span> <span style="color:{PALETTE["text_main"]};">{message}</span>'
        self.log_view.append(html)
        # Автопрокрутка вниз
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Завершение работы ─────────────────────────────────────────────────────

    def closeEvent(self, event):
        """Корректно останавливаем все активные потоки перед закрытием."""
        self._timer.stop()
        with self._lock:
            workers = list(self._workers.values())

        for w in workers:
            w.stop()

        # Ждём завершения потоков (с таймаутом)
        for w in workers:
            w.wait(msecs=3000)

        self._save_config()
        event.accept()


# ─── Точка входа ──────────────────────────────────────────────────────────────

def main():
    # Высокое DPI на Windows
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("NRK Manager")
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("NRK")

    # Применяем глобальную тему
    app.setStyleSheet(QSS)

    # Устанавливаем тёмную палитру системным виджетам
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(PALETTE["bg_deep"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(PALETTE["text_main"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(PALETTE["bg_panel"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(PALETTE["bg_row_alt"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(PALETTE["text_main"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(PALETTE["btn_bg"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(PALETTE["text_main"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(PALETTE["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(PALETTE["text_main"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(PALETTE["bg_panel"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(PALETTE["text_main"]))
    app.setPalette(palette)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()