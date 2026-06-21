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
import urllib.request
import urllib.error

# PyQt6-WebEngine — опциональная зависимость
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QHeaderView, QDialog, QFormLayout, QDialogButtonBox, QTextEdit,
    QSplitter, QMessageBox, QMenu, QAbstractItemView, QStatusBar,
    QFrame, QSizePolicy, QScrollArea, QGridLayout,
    QTabWidget, QTabBar, QToolButton
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSortFilterProxyModel,
    QItemSelectionModel, QSize, QPropertyAnimation, QEasingCurve
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

GITHUB_REPO   = "MuxaeLka/RaspbeNRK"
GITHUB_API    = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
VIEW_GRID     = "grid"   # режим карточек
VIEW_TABLE    = "table"  # режим таблицы
APP_VERSION = "1.0.5"

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
    font-family: 'Segoe UI Variable', 'Segoe UI', 'Inter', sans-serif;
    font-size: 12px;
    letter-spacing: 0.1px;
}}

/* ── Карточки устройств ────────────────────────────────── */
QFrame#device_card {{
    background-color: {PALETTE['bg_panel']};
    border: 1px solid {PALETTE['border']};
    border-radius: 10px;
}}

QFrame#device_card:hover {{
    border-color: {PALETTE['text_dim']};
}}

QLabel#card_name {{
    font-size: 12px;
    font-weight: 600;
    color: {PALETTE['text_main']};
}}

QLabel#card_ip {{
    font-size: 10px;
    color: {PALETTE['text_dim']};
    font-family: 'Consolas', monospace;
}}

QLabel#card_ping {{
    font-size: 10px;
    color: {PALETTE['text_dim']};
}}

QLabel#card_type {{
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0.6px;
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

/* ── Браузерные вкладки ───────────────────────────────── */
QTabWidget::pane {{
    border: none;
    background: {PALETTE['bg_deep']};
}}

QTabBar {{
    background: {PALETTE['bg_panel']};
}}

QTabBar::tab {{
    background: {PALETTE['bg_panel']};
    color: {PALETTE['text_dim']};
    border: none;
    border-right: 1px solid {PALETTE['border']};
    padding: 7px 14px;
    font-size: 11px;
    min-width: 120px;
    max-width: 220px;
}}

QTabBar::tab:selected {{
    background: {PALETTE['bg_deep']};
    color: {PALETTE['text_main']};
    border-bottom: 2px solid {PALETTE['accent']};
}}

QTabBar::tab:hover:!selected {{
    background: {PALETTE['btn_hover']};
    color: {PALETTE['text_main']};
}}

QTabBar::close-button {{
    image: none;
    subcontrol-position: right;
}}

QToolButton#nav_btn {{
    background: {PALETTE['bg_panel']};
    color: {PALETTE['text_main']};
    border: none;
    border-right: 1px solid {PALETTE['border']};
    padding: 4px 10px;
    font-size: 14px;
}}

QToolButton#nav_btn:hover {{
    background: {PALETTE['btn_hover']};
}}

QLineEdit#url_bar {{
    background: {PALETTE['bg_deep']};
    color: {PALETTE['text_main']};
    border: 1px solid {PALETTE['border']};
    border-radius: 4px;
    padding: 4px 10px;
    font-family: 'Consolas', monospace;
    font-size: 11px;
}}

QLineEdit#url_bar:focus {{
    border-color: {PALETTE['accent']};
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

# Реестр типов устройств — расширяемый пользователем
# Ключ = внутренний ID типа, значение = параметры
DEVICE_TYPES: dict = {
    "raspberry": {"label": "Raspberry Pi", "color": "#e67e22", "default_port": 8080, "icon": "🍓"},
    "mikrotik":  {"label": "MikroTik",     "color": "#388bfd", "default_port": 80,   "icon": "🔷"},
}

# Встроенные типы нельзя удалить
BUILTIN_TYPES = {"raspberry", "mikrotik"}

# Доступные иконки для выбора в диалоге
ICON_OPTIONS = [
    "🍓", "🔷", "📡", "🖥️", "💻", "🖨️", "📷", "🔌",
    "⚙️", "🔧", "🌐", "📶", "🛰️", "🤖", "🔒", "💾",
]


class Device:
    """Одно устройство с состоянием мониторинга. Поддерживает Raspberry Pi и MikroTik."""

    def __init__(self, name: str, ip: str, port: int = WEB_PORT,
                 device_type: str = "raspberry", icon: str = ""):
        self.name = name
        self.ip = ip
        self.port = port
        self.device_type = device_type  # "raspberry" | "mikrotik" | custom
        self.icon = icon  # индивидуальная иконка (emoji); если пусто — берём из типа
        self.online: bool | None = None   # None = ещё не проверяли
        self.ping_ms: float | None = None
        self.last_seen: datetime | None = None

    def web_url(self) -> str:
        """URL для открытия в браузере."""
        return f"http://{self.ip}:{self.port}"

    def type_label(self) -> str:
        return DEVICE_TYPES.get(self.device_type, {}).get("label", self.device_type)

    def type_color(self) -> str:
        return DEVICE_TYPES.get(self.device_type, {}).get("color", PALETTE["text_dim"])

    def type_icon(self) -> str:
        return DEVICE_TYPES.get(self.device_type, {}).get("icon", "📡")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ip": self.ip,
            "port": self.port,
            "device_type": self.device_type,
            "icon": self.icon,
        }

    @staticmethod
    def from_dict(d: dict) -> "Device":
        return Device(
            name=d["name"],
            ip=d["ip"],
            port=d.get("port", WEB_PORT),
            device_type=d.get("device_type", "raspberry"),
            icon=d.get("icon", ""),
        )

    def effective_icon(self) -> str:
        """Иконка устройства: индивидуальная если задана, иначе из типа."""
        return self.icon if self.icon else self.type_icon()

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
        combo_style = (
            f"QComboBox {{ background:{PALETTE['bg_panel']}; color:{PALETTE['text_main']};"
            f"border:1px solid {PALETTE['border']}; border-radius:6px; padding:6px 10px;}}"
            f"QComboBox::drop-down {{ border:none; }}"
            f"QComboBox QAbstractItemView {{ background:{PALETTE['bg_panel']};"
            f"color:{PALETTE['text_main']}; selection-background-color:{PALETTE['bg_selected']};}}"
        )

        # Тип устройства — заполняется динамически при открытии (см. showEvent)
        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet(combo_style)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        self._populate_type_combo()  # первичное заполнение

        # Индивидуальная иконка устройства
        self.icon_combo = QComboBox()
        self.icon_combo.setStyleSheet(combo_style)
        self.icon_combo.setFixedWidth(90)
        for ico in ICON_OPTIONS:
            self.icon_combo.addItem(ico, ico)

        if device:
            self.name_edit.setText(device.name)
            self.ip_edit.setText(device.ip)
            self.port_edit.setText(str(device.port))
            idx = self.type_combo.findData(device.device_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            # Иконка устройства
            ico_idx = self.icon_combo.findData(getattr(device, "icon", device.type_icon()))
            if ico_idx >= 0:
                self.icon_combo.setCurrentIndex(ico_idx)
        else:
            self.port_edit.setText("8080")
            # Дефолтная иконка по типу
            self._sync_icon_from_type()

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"color:{PALETTE['text_dim']};")
            return l

        # Иконка + тип в одну строку
        type_row = QHBoxLayout()
        type_row.setSpacing(8)
        type_row.addWidget(self.icon_combo)
        type_row.addWidget(self.type_combo)

        form.addRow(lbl("Название:"),  self.name_edit)
        form.addRow(lbl("IP-адрес:"),  self.ip_edit)
        form.addRow(lbl("Порт:"),      self.port_edit)
        form.addRow(lbl("Тип / иконка:"), type_row)
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

    def _populate_type_combo(self):
        """Заполнить type_combo из актуального DEVICE_TYPES.
        Вызывается при создании и при каждом открытии диалога —
        чтобы новые типы из реестра сразу появлялись в списке."""
        # Запоминаем текущий выбор
        current = self.type_combo.currentData()
        self.type_combo.blockSignals(True)
        self.type_combo.clear()
        for key, val in DEVICE_TYPES.items():
            self.type_combo.addItem(f"{val.get('icon', '📡')}  {val['label']}", key)
        # Восстанавливаем выбор
        if current:
            idx = self.type_combo.findData(current)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        self.type_combo.blockSignals(False)

    def showEvent(self, event):
        """При каждом показе диалога обновляем список типов."""
        self._populate_type_combo()
        super().showEvent(event)

    def _on_type_changed(self, _idx: int):
        """При смене типа подставляем дефолтный порт и синхронизируем иконку."""
        dtype = self.type_combo.currentData()
        default_port = DEVICE_TYPES.get(dtype, {}).get("default_port", 80)
        current = self.port_edit.text().strip()
        known_defaults = {str(v["default_port"]) for v in DEVICE_TYPES.values()}
        if not current or current in known_defaults:
            self.port_edit.setText(str(default_port))
        self._sync_icon_from_type()
        self._update_hint()

    def _sync_icon_from_type(self):
        """Подставить иконку по умолчанию для текущего типа."""
        dtype = self.type_combo.currentData()
        default_icon = DEVICE_TYPES.get(dtype, {}).get("icon", "📡")
        idx = self.icon_combo.findData(default_icon)
        if idx >= 0:
            self.icon_combo.setCurrentIndex(idx)

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

    def get_values(self) -> tuple[str, str, int, str, str]:
        return (
            self.name_edit.text().strip(),
            self.ip_edit.text().strip(),
            int(self.port_edit.text().strip()),
            self.type_combo.currentData(),
            self.icon_combo.currentData(),
        )


# ─── Карточка устройства (Grid-вид) ───────────────────────────────────────────

class DeviceCard(QFrame):
    """
    Карточка одного устройства для Grid-вида.
    Красное свечение = офлайн, мигающее зелёное = онлайн.
    Двойной клик = открыть устройство.
    """
    double_clicked = pyqtSignal(object)  # передаёт Device

    # Цвета свечения
    GLOW_ONLINE  = "0 0 12px 3px rgba(63, 185, 80, 0.75)"
    GLOW_OFFLINE = "0 0 12px 3px rgba(248, 81, 73, 0.65)"
    GLOW_NONE    = "none"

    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.device = device
        self.setObjectName("device_card")
        self.setFixedSize(170, 140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Таймер мигания (онлайн)
        self._blink_state = True
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink_tick)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 10)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Иконка (emoji как текст — без доп. зависимостей)
        self._icon_lbl = QLabel()
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet("font-size: 28px; background: transparent;")
        layout.addWidget(self._icon_lbl)

        # Название
        self._name_lbl = QLabel()
        self._name_lbl.setObjectName("card_name")
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_lbl.setWordWrap(True)
        layout.addWidget(self._name_lbl)

        # IP
        self._ip_lbl = QLabel()
        self._ip_lbl.setObjectName("card_ip")
        self._ip_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._ip_lbl)

        # Тип
        self._type_lbl = QLabel()
        self._type_lbl.setObjectName("card_type")
        self._type_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._type_lbl)

        # Отклик / статус
        self._ping_lbl = QLabel()
        self._ping_lbl.setObjectName("card_ping")
        self._ping_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._ping_lbl)

        self.refresh()

    def refresh(self):
        """Обновить отображение из device.online / device.ping_ms."""
        d = self.device
        # Индивидуальная иконка или из реестра типов
        self._icon_lbl.setText(d.effective_icon())

        self._name_lbl.setText(d.name)
        self._ip_lbl.setText(d.ip)
        self._type_lbl.setText(d.type_label().upper())
        self._type_lbl.setStyleSheet(
            f"font-size:9px; font-weight:600; letter-spacing:0.6px;"
            f"color:{d.type_color()}; background:transparent;"
        )

        # Статус и свечение
        if d.online is None:
            self._ping_lbl.setText("⏳ проверка...")
            self._ping_lbl.setStyleSheet(f"color:{PALETTE['text_dim']}; background:transparent;")
            self._set_glow("none")
            self._blink_timer.stop()
        elif d.online:
            ping = f"{d.ping_ms} мс" if d.ping_ms is not None else ""
            self._ping_lbl.setText(f"● {ping}")
            self._ping_lbl.setStyleSheet(f"color:{PALETTE['online']}; font-size:10px; background:transparent;")
            self._blink_timer.start(800)  # мигаем каждые 800 мс
        else:
            self._ping_lbl.setText("● офлайн")
            self._ping_lbl.setStyleSheet(f"color:{PALETTE['offline']}; font-size:10px; background:transparent;")
            self._set_glow("offline")
            self._blink_timer.stop()

    def _blink_tick(self):
        """Чередуем свечение вкл/выкл для онлайн-эффекта."""
        self._blink_state = not self._blink_state
        self._set_glow("online" if self._blink_state else "none")

    def _set_glow(self, state: str):
        """Применяем box-shadow через stylesheet."""
        if state == "online":
            shadow = f"border: 1px solid {PALETTE['online']}; border-radius: 10px; background-color: {PALETTE['bg_panel']};"
        elif state == "offline":
            shadow = f"border: 1px solid {PALETTE['offline']}; border-radius: 10px; background-color: {PALETTE['bg_panel']};"
        else:
            shadow = f"border: 1px solid {PALETTE['border']}; border-radius: 10px; background-color: {PALETTE['bg_panel']};"
        self.setStyleSheet(f"QFrame#device_card {{ {shadow} }}")

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.device)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        # Пробрасываем в MainWindow через сигнал
        self.double_clicked.emit(self.device)  # просто открываем


# ─── Поток проверки обновлений ─────────────────────────────────────────────────

class UpdateChecker(QThread):
    """Проверяет последний релиз на GitHub и сигнализирует если есть новая версия."""
    update_available = pyqtSignal(str, str)  # (latest_version, download_url)
    no_update = pyqtSignal()

    def run(self):
        try:
            req = urllib.request.Request(
                GITHUB_API,
                headers={"User-Agent": f"NRK-Manager/{APP_VERSION}"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                import json as _json
                data = _json.loads(resp.read().decode())
            tag = data.get("tag_name", "").lstrip("v")
            assets = data.get("assets", [])
            url = next((a["browser_download_url"] for a in assets
                        if a["name"].endswith(".exe")), "")

            # Сравниваем версии как кортежи чисел, а не строки
            # "1.0.9" < "1.0.10" — строковое сравнение даст неверный результат
            def ver_tuple(v: str):
                try:
                    return tuple(int(x) for x in v.split("."))
                except ValueError:
                    return (0,)

            if tag and ver_tuple(tag) > ver_tuple(APP_VERSION) and url:
                self.update_available.emit(tag, url)
            else:
                self.no_update.emit()
        except Exception:
            self.no_update.emit()




# ─── Виджет вкладки встроенного браузера ──────────────────────────────────────

class BrowserTab(QWidget):
    """
    Одна вкладка встроенного браузера.
    Содержит адресную строку, кнопки навигации и QWebEngineView.
    Если WebEngine недоступен — показывает заглушку с кнопкой открыть в браузере.
    """
    title_changed = pyqtSignal(str)   # для обновления заголовка вкладки

    def __init__(self, url: str, device_name: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.device_name = device_name

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Навигационная панель ───────────────────────────────────────────
        nav_bar = QWidget()
        nav_bar.setFixedHeight(36)
        nav_bar.setStyleSheet(
            f"background:{PALETTE['bg_panel']}; border-bottom:1px solid {PALETTE['border']};"
        )
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(4, 2, 4, 2)
        nav_layout.setSpacing(2)

        def nav_btn(text, tooltip=""):
            b = QToolButton()
            b.setText(text)
            b.setObjectName("nav_btn")
            b.setFixedSize(32, 28)
            if tooltip:
                b.setToolTip(tooltip)
            return b

        self.btn_back    = nav_btn("←", "Назад")
        self.btn_forward = nav_btn("→", "Вперёд")
        self.btn_reload  = nav_btn("⟳", "Обновить")
        self.btn_home    = nav_btn("⌂", "На главную")
        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.btn_forward)
        nav_layout.addWidget(self.btn_reload)
        nav_layout.addWidget(self.btn_home)

        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("url_bar")
        self.url_bar.setText(url)
        self.url_bar.returnPressed.connect(self._navigate_to_url)
        nav_layout.addWidget(self.url_bar, stretch=1)

        self.btn_external = nav_btn("⬡", "Открыть в системном браузере")
        self.btn_external.clicked.connect(self._open_external)
        nav_layout.addWidget(self.btn_external)

        layout.addWidget(nav_bar)

        # ── Контент ────────────────────────────────────────────────────────
        if WEBENGINE_AVAILABLE:
            self.view = QWebEngineView()
            self.view.load(__import__('PyQt6.QtCore', fromlist=['QUrl']).QUrl(url))
            self.view.urlChanged.connect(self._on_url_changed)
            self.view.titleChanged.connect(self._on_title_changed)
            self.view.loadProgress.connect(self._on_load_progress)

            # Подключаем кнопки навигации
            self.btn_back.clicked.connect(self.view.back)
            self.btn_forward.clicked.connect(self.view.forward)
            self.btn_reload.clicked.connect(self.view.reload)
            self.btn_home.clicked.connect(lambda: self.view.load(
                __import__('PyQt6.QtCore', fromlist=['QUrl']).QUrl(self.url)
            ))
            layout.addWidget(self.view)
        else:
            # Заглушка если PyQt6-WebEngine не установлен
            placeholder = QWidget()
            placeholder.setStyleSheet(f"background:{PALETTE['bg_deep']};")
            ph_layout = QVBoxLayout(placeholder)
            ph_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            ico = QLabel("🌐")
            ico.setStyleSheet("font-size:48px; background:transparent;")
            ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ph_layout.addWidget(ico)

            msg = QLabel(
                "Встроенный браузер недоступен.\n\n"
                "Установите PyQt6-WebEngine:\n"
                "pip install PyQt6-WebEngine\n\n"
                "или откройте в системном браузере:"
            )
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setStyleSheet(f"color:{PALETTE['text_dim']}; font-size:13px; background:transparent;")
            ph_layout.addWidget(msg)

            open_btn = QPushButton(f"Открыть {url}")
            open_btn.setObjectName("primary")
            open_btn.setFixedWidth(300)
            open_btn.clicked.connect(self._open_external)
            ph_layout.addWidget(open_btn, alignment=Qt.AlignmentFlag.AlignCenter)

            layout.addWidget(placeholder)
            self.view = None

            # Кнопки навигации недоступны без WebEngine
            for b in [self.btn_back, self.btn_forward, self.btn_reload, self.btn_home]:
                b.setEnabled(False)

    def _navigate_to_url(self):
        if self.view:
            from PyQt6.QtCore import QUrl
            url = self.url_bar.text().strip()
            if not url.startswith("http"):
                url = "http://" + url
            self.view.load(QUrl(url))

    def _on_url_changed(self, qurl):
        self.url_bar.setText(qurl.toString())

    def _on_title_changed(self, title: str):
        # Обрезаем длинные заголовки для вкладки
        short = (title[:18] + "…") if len(title) > 20 else title
        self.title_changed.emit(short or self.device_name)

    def _on_load_progress(self, progress: int):
        # Показываем прогресс в адресной строке через placeholder
        if progress < 100:
            self.url_bar.setPlaceholderText(f"Загрузка {progress}%...")
        else:
            self.url_bar.setPlaceholderText("")

    def _open_external(self):
        import webbrowser as _wb
        _wb.open(self.url_bar.text() or self.url)


# ─── Панель встроенного браузера ──────────────────────────────────────────────

class BrowserPanel(QWidget):
    """
    Панель встроенного браузера с вкладками.
    Каждое устройство открывается в отдельной вкладке.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.setStyleSheet("")  # используем глобальный QSS
        layout.addWidget(self.tabs)

        # Кнопка закрытия панели браузера
        self._close_all_btn = QPushButton("✕  Закрыть браузер")
        self._close_all_btn.setFixedHeight(28)
        self._close_all_btn.setStyleSheet(
            f"font-size:11px; color:{PALETTE['text_dim']};"
            f"background:{PALETTE['bg_panel']}; border:none;"
            f"border-top:1px solid {PALETTE['border']}; border-radius:0;"
        )
        self._close_all_btn.clicked.connect(self._do_hide)
        layout.addWidget(self._close_all_btn)


    def _do_hide(self):
        self.setVisible(False)

    def open_url(self, url: str, device_name: str):
        """Открыть URL — если вкладка уже есть (по URL), переключиться на неё."""
        # Ищем существующую вкладку
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, BrowserTab) and tab.url == url:
                self.tabs.setCurrentIndex(i)
                return

        # Создаём новую вкладку
        tab = BrowserTab(url, device_name)
        tab.title_changed.connect(lambda title, i=None: self._update_tab_title(tab, title))
        idx = self.tabs.addTab(tab, f"⏳ {device_name}")
        self.tabs.setCurrentIndex(idx)

    def _update_tab_title(self, tab: "BrowserTab", title: str):
        idx = self.tabs.indexOf(tab)
        if idx >= 0:
            self.tabs.setTabText(idx, title)

    def _close_tab(self, idx: int):
        widget = self.tabs.widget(idx)
        self.tabs.removeTab(idx)
        if widget:
            widget.deleteLater()


# ─── Диалог реестра типов устройств ───────────────────────────────────────────

class TypeRegistryDialog(QDialog):
    """
    Управление реестром типов устройств.
    Позволяет добавлять и удалять пользовательские типы.
    Встроенные типы (raspberry, mikrotik) защищены от удаления.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Реестр типов устройств")
        self.setModal(True)
        self.setMinimumSize(500, 380)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Заголовок
        title = QLabel("Типы устройств")
        title.setStyleSheet(f"font-size:15px; font-weight:700; color:{PALETTE['text_main']};")
        layout.addWidget(title)

        sub = QLabel("Встроенные типы защищены от удаления. "
                     "Добавленные типы сохраняются в config.json.")
        sub.setStyleSheet(f"font-size:11px; color:{PALETTE['text_dim']};")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # Таблица типов
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Иконка", "Порт", "Цвет"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            f"QTableWidget {{alternate-background-color: {PALETTE['bg_row_alt']};}}"
        )
        layout.addWidget(self.table)

        # Кнопки
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("+ Добавить тип")
        self.btn_add.clicked.connect(self._add_type)
        self.btn_del = QPushButton("Удалить")
        self.btn_del.setObjectName("danger")
        self.btn_del.clicked.connect(self._delete_type)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_del)
        btn_row.addStretch()
        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("primary")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(0)
        self.table.setRowCount(len(DEVICE_TYPES))
        for row, (key, val) in enumerate(DEVICE_TYPES.items()):
            builtin = key in BUILTIN_TYPES

            id_item = QTableWidgetItem(key)
            id_item.setForeground(QBrush(QColor(
                PALETTE["text_dim"] if builtin else PALETTE["text_main"]
            )))
            self.table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem(val["label"])
            if builtin:
                name_item.setForeground(QBrush(QColor(PALETTE["text_dim"])))
            self.table.setItem(row, 1, name_item)

            icon_item = QTableWidgetItem(val.get("icon", "📡"))
            icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, icon_item)

            port_item = QTableWidgetItem(str(val["default_port"]))
            port_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, port_item)

            color_item = QTableWidgetItem(val["color"])
            color_item.setForeground(QBrush(QColor(val["color"])))
            color_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, color_item)

            # Встроенные — серый фон
            if builtin:
                for col in range(5):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QBrush(QColor(PALETTE["bg_row_alt"])))

            self.table.setRowHeight(row, 36)

    def _add_type(self):
        dlg = AddTypeDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            key, label, icon, port, color = dlg.get_values()
            if key in DEVICE_TYPES:
                QMessageBox.warning(self, "Ошибка", f"Тип с ID '{key}' уже существует.")
                return
            DEVICE_TYPES[key] = {
                "label": label,
                "icon": icon,
                "default_port": port,
                "color": color,
            }
            self._refresh_table()

    def _delete_type(self):
        row = self.table.currentRow()
        if row < 0:
            return
        key = self.table.item(row, 0).text()
        if key in BUILTIN_TYPES:
            QMessageBox.warning(self, "Защищено",
                                f"Тип '{key}' встроенный и не может быть удалён.")
            return
        reply = QMessageBox.question(
            self, "Удалить тип",
            f"Удалить тип '{key}'?\n\n"
            f"Устройства с этим типом сохранят тип как ID.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            DEVICE_TYPES.pop(key, None)
            self._refresh_table()


# ─── Диалог добавления нового типа ────────────────────────────────────────────

class AddTypeDialog(QDialog):
    """Форма для добавления нового пользовательского типа устройства."""

    # Палитра цветов для выбора
    COLOR_OPTIONS = [
        "#e67e22", "#388bfd", "#3fb950", "#f85149", "#d29922",
        "#a371f7", "#39d353", "#58a6ff", "#ff7b72", "#ffa657",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить тип устройства")
        self.setModal(True)
        self.setMinimumWidth(360)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Новый тип устройства")
        title.setStyleSheet(f"font-size:14px; font-weight:700; color:{PALETTE['text_main']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"color:{PALETTE['text_dim']};")
            return l

        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("camera, switch, sensor ...")
        form.addRow(lbl("ID (латиница):"), self.id_edit)

        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("IP Camera")
        form.addRow(lbl("Название:"), self.label_edit)

        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("80")
        self.port_edit.setText("80")
        form.addRow(lbl("Порт:"), self.port_edit)

        # Иконка
        combo_style = (
            f"QComboBox {{ background:{PALETTE['bg_panel']}; color:{PALETTE['text_main']};"
            f"border:1px solid {PALETTE['border']}; border-radius:6px; padding:6px 10px;}}"
            f"QComboBox::drop-down {{ border:none; }}"
            f"QComboBox QAbstractItemView {{ background:{PALETTE['bg_panel']};"
            f"color:{PALETTE['text_main']}; selection-background-color:{PALETTE['bg_selected']};}}"
        )
        self.icon_combo = QComboBox()
        self.icon_combo.setStyleSheet(combo_style)
        for ico in ICON_OPTIONS:
            self.icon_combo.addItem(ico, ico)
        form.addRow(lbl("Иконка:"), self.icon_combo)

        # Цвет
        self.color_combo = QComboBox()
        self.color_combo.setStyleSheet(combo_style)
        for color in self.COLOR_OPTIONS:
            self.color_combo.addItem(color, color)
            idx = self.color_combo.count() - 1
            self.color_combo.setItemData(
                idx, QBrush(QColor(color)), Qt.ItemDataRole.ForegroundRole
            )
        form.addRow(lbl("Цвет:"), self.color_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("primary")
        layout.addWidget(buttons)

    def _on_accept(self):
        key = self.id_edit.text().strip().lower().replace(" ", "_")
        label = self.label_edit.text().strip()
        port = self.port_edit.text().strip()
        if not key or not label:
            QMessageBox.warning(self, "Ошибка", "Заполните ID и название.")
            return
        if not key.isidentifier():
            QMessageBox.warning(self, "Ошибка",
                                "ID должен содержать только латинские буквы, цифры и _")
            return
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            QMessageBox.warning(self, "Ошибка", "Порт: число от 1 до 65535.")
            return
        self.accept()

    def get_values(self) -> tuple[str, str, str, int, str]:
        return (
            self.id_edit.text().strip().lower().replace(" ", "_"),
            self.label_edit.text().strip(),
            self.icon_combo.currentData(),
            int(self.port_edit.text().strip()),
            self.color_combo.currentData(),
        )

# ─── Виджет заголовка ─────────────────────────────────────────────────────────

class HeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setStyleSheet(
            f"background-color:{PALETTE['bg_panel']};"
            f"border-bottom:1px solid {PALETTE['border']};"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 0, 16, 0)
        row.setSpacing(10)

        # Иконка — создаём через QPixmap напрямую без make_app_icon()
        # чтобы не зависеть от порядка инициализации QApplication
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setStyleSheet(
            f"background:{PALETTE['accent']}; border-radius:8px;"
            f"color:#ffffff; font-size:16px; font-weight:700;"
        )
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setText("N")
        row.addWidget(icon_lbl)

        # Текстовый блок
        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.setContentsMargins(0, 0, 0, 0)

        t = QLabel("NRK Manager")
        t.setStyleSheet(
            f"font-size:15px; font-weight:700; color:{PALETTE['text_main']};"
            f"background:transparent; border:none;"
        )
        sub = QLabel("Менеджер Raspberry Pi через WireGuard")
        sub.setStyleSheet(
            f"font-size:10px; color:{PALETTE['text_dim']};"
            f"background:transparent; border:none;"
        )
        text_col.addWidget(t)
        text_col.addWidget(sub)
        row.addLayout(text_col)

        row.addStretch()

        # Статус онлайн
        self.status_lbl = QLabel("● Ожидание...")
        self.status_lbl.setFixedHeight(24)
        self.status_lbl.setStyleSheet(
            f"color:{PALETTE['text_dim']}; font-size:12px;"
            f"background:transparent; border:none;"
        )
        row.addWidget(self.status_lbl)

    def set_status(self, online: int, total: int):
        color = PALETTE["online"] if online == total else (
            PALETTE["warn"] if online > 0 else PALETTE["offline"]
        )
        self.status_lbl.setText(f"● {online}/{total} онлайн")
        self.status_lbl.setStyleSheet(
            f"color:{color}; font-size:12px; font-weight:600;"
            f"background:transparent; border:none;"
        )

# ─── Главное окно ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"NRK Manager v{APP_VERSION}")
        self.setMinimumSize(900, 620)
        self.resize(1100, 700)
        self.setWindowIcon(make_app_icon())

        # Режим отображения
        self._view_mode = VIEW_GRID  # grid | table

        # Устройства и воркеры
        self.devices: list[Device] = []
        self._workers: dict[str, PingWorker] = {}   # ip -> worker
        self._lock = threading.Lock()               # для безопасного доступа к workers
        self._cards: dict[str, DeviceCard] = {}     # ip -> DeviceCard

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
        if not WEBENGINE_AVAILABLE:
            self._log("Встроенный браузер недоступен. Установите: pip install PyQt6-WebEngine", error=True)

        # Проверка обновлений
        self._update_checker = UpdateChecker()
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.start()

    # ── Загрузка/сохранение конфига ───────────────────────────────────────────

    def _load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                # Загружаем пользовательские типы устройств
                for key, val in data.get("device_types", {}).items():
                    if key not in DEVICE_TYPES:
                        DEVICE_TYPES[key] = val
                self.devices = [Device.from_dict(d) for d in data.get("devices", [])]
                return
            except Exception as e:
                print(f"[config] Ошибка чтения: {e}")
        # Файл отсутствует или повреждён — используем дефолт
        self.devices = [Device.from_dict(d) for d in DEFAULT_DEVICES]
        self._save_config()

    def _save_config(self):
        try:
            # Сохраняем только пользовательские типы (не встроенные)
            custom_types = {k: v for k, v in DEVICE_TYPES.items()
                            if k not in BUILTIN_TYPES}
            data = {
                "devices": [d.to_dict() for d in self.devices],
                "device_types": custom_types,
            }
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

        # Горизонтальный сплиттер: левая панель (таблица/grid) + браузер
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.h_splitter.setHandleWidth(4)
        root.addWidget(self.h_splitter)

        # Левая часть: вертикальный сплиттер (таблица + лог)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Сплиттер: таблица + лог
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(4)
        left_layout.addWidget(splitter)
        self.h_splitter.addWidget(left_widget)

        # Браузерная панель (справа, скрыта по умолчанию)
        self.browser_panel = BrowserPanel()
        self.browser_panel.setMinimumWidth(400)
        self.browser_panel.setVisible(False)
        self.h_splitter.addWidget(self.browser_panel)
        self.h_splitter.setStretchFactor(0, 1)
        self.h_splitter.setStretchFactor(1, 2)

        # Верхняя часть: тулбар + таблица
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(12, 12, 12, 8)
        top_layout.setSpacing(10)

        # Тулбар
        toolbar = self._build_toolbar()
        top_layout.addLayout(toolbar)

        # ── Grid-вид (карточки) ──────────────────────────────────────────
        self.grid_scroll = QScrollArea()
        self.grid_scroll.setWidgetResizable(True)
        self.grid_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.grid_scroll.setStyleSheet(f"background:{PALETTE['bg_deep']}; border:none;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet(f"background:{PALETTE['bg_deep']};")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        self.grid_layout.setSpacing(12)
        self.grid_scroll.setWidget(self.grid_container)
        top_layout.addWidget(self.grid_scroll)

        # ── Таблица
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

        # Показываем нужный вид
        self._apply_view_mode()
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

        self.btn_types = btn("⚙ Типы", tooltip="Управление реестром типов устройств")
        self.btn_types.clicked.connect(self._open_type_registry)
        tb.addWidget(self.btn_types)

        # Разделитель
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet(f"color:{PALETTE['border']};")
        tb.addWidget(sep2)

        # Переключатель вида
        self.btn_view = btn("⊞  Grid", tooltip="Переключить вид: карточки / таблица")
        self.btn_view.setFixedWidth(80)
        self.btn_view.clicked.connect(self._toggle_view)
        tb.addWidget(self.btn_view)

        self.btn_browser = btn("🌐  Браузер", tooltip="Показать/скрыть встроенный браузер")
        self.btn_browser.setFixedWidth(100)
        self.btn_browser.clicked.connect(self._toggle_browser)
        tb.addWidget(self.btn_browser)

        return tb

    # ── Заполнение таблицы ────────────────────────────────────────────────────

    def _populate_table(self):
        """Перестроить таблицу и grid из списка self.devices с учётом фильтра."""
        query = self.search_edit.text().strip().lower() if hasattr(self, "search_edit") else ""

        visible = [d for d in self.devices if
                   not query or query in d.name.lower() or query in d.ip.lower()]

        # ── Таблица
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.table.setRowCount(len(visible))
        for row, device in enumerate(visible):
            self._set_row(row, device)
        self.table.setSortingEnabled(True)

        # ── Grid
        self._rebuild_grid(visible)

        self._update_header_status()

    def _rebuild_grid(self, visible: list):
        """Перестроить карточки в grid-контейнере."""
        # Удаляем старые карточки
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        cols = max(1, self.grid_scroll.width() // 190) if hasattr(self, 'grid_scroll') else 5
        for idx, device in enumerate(visible):
            card = DeviceCard(device)
            card.double_clicked.connect(self._open_device)
            self._cards[device.ip] = card
            self.grid_layout.addWidget(card, idx // cols, idx % cols)

        # Распорка снизу чтобы карточки не растягивались
        self.grid_layout.setRowStretch(len(visible) // cols + 1, 1)

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


    def _open_in_browser(self, device: Device):
        """Принудительно открыть устройство во встроенном браузере."""
        if not self.browser_panel.isVisible():
            self.browser_panel.setVisible(True)
            self.btn_browser.setText("✕  Браузер")
        self.browser_panel.open_url(device.web_url(), device.name)
        if not WEBENGINE_AVAILABLE:
            self._log("WebEngine недоступен. pip install PyQt6-WebEngine", error=True)

    def _toggle_browser(self):
        """Показать/скрыть панель встроенного браузера."""
        visible = not self.browser_panel.isVisible()
        self.browser_panel.setVisible(visible)
        self.btn_browser.setText("✕  Браузер" if visible else "🌐  Браузер")
        if visible and not WEBENGINE_AVAILABLE:
            self._log(
                "WebEngine недоступен. Установите: pip install PyQt6-WebEngine",
                error=True
            )

    def _open_type_registry(self):
        """Открыть диалог реестра типов. После закрытия — обновить комбо в диалогах."""
        dlg = TypeRegistryDialog(self)
        dlg.exec()
        # Сохраняем новые типы в конфиг
        self._save_config()
        self._log(f"Реестр типов обновлён. Типов: {len(DEVICE_TYPES)}")

    # ── Переключение вида ─────────────────────────────────────────────────────

    def _toggle_view(self):
        self._view_mode = VIEW_TABLE if self._view_mode == VIEW_GRID else VIEW_GRID
        self._apply_view_mode()
        # Перестраиваем grid при переключении (чтобы правильно рассчитать cols)
        if self._view_mode == VIEW_GRID:
            query = self.search_edit.text().strip().lower()
            visible = [d for d in self.devices if
                       not query or query in d.name.lower() or query in d.ip.lower()]
            self._rebuild_grid(visible)

    def _apply_view_mode(self):
        is_grid = self._view_mode == VIEW_GRID
        self.grid_scroll.setVisible(is_grid)
        self.table.setVisible(not is_grid)
        if hasattr(self, 'btn_view'):
            self.btn_view.setText("≡  Table" if is_grid else "⊞  Grid")

    # ── Авто-апдейтер ─────────────────────────────────────────────────────────

    def _on_update_available(self, version: str, url: str):
        """Показываем уведомление о новой версии."""
        self._log(f"Доступна новая версия v{version}!", error=False)
        reply = QMessageBox.question(
            self,
            "Обновление доступно",
            f"Доступна версия v{version}.\n\n"
            f"Текущая версия: v{APP_VERSION}\n\n"
            f"Открыть страницу загрузки?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            webbrowser.open(url)

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

        # Обновляем карточку в grid-виде
        if hasattr(self, '_cards') and ip in self._cards:
            self._cards[ip].refresh()

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
        self._log(f"Открываем: {url}")
        if hasattr(self, 'browser_panel') and self.browser_panel.isVisible():
            # Открываем во встроенном браузере
            self.browser_panel.open_url(url, device.name)
        else:
            # Системный браузер
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

        act_open_ext = QAction("Открыть в системном браузере", self)
        act_open_ext.triggered.connect(lambda: webbrowser.open(device.web_url()))
        menu.addAction(act_open_ext)

        act_open_int = QAction("Открыть во встроенном браузере", self)
        act_open_int.triggered.connect(lambda: self._open_in_browser(device))
        menu.addAction(act_open_int)

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
            name, ip, port, dtype, icon = dlg.get_values()
            if any(d.ip == ip for d in self.devices):
                QMessageBox.warning(self, "Дубликат", f"Устройство с IP {ip} уже существует.")
                return
            device = Device(name, ip, port, dtype, icon)
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
            new_name, new_ip, new_port, new_type, new_icon = dlg.get_values()
            if new_ip != old_ip and any(d.ip == new_ip for d in self.devices):
                QMessageBox.warning(self, "Дубликат", f"Устройство с IP {new_ip} уже существует.")
                return
            device.name = new_name
            device.ip = new_ip
            device.port = new_port
            device.device_type = new_type
            device.icon = new_icon
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

    def resizeEvent(self, event):
        """При изменении ширины окна перестраиваем grid чтобы колонки пересчитались."""
        super().resizeEvent(event)
        if self._view_mode == VIEW_GRID and hasattr(self, '_cards') and self._cards:
            query = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ''
            visible = [d for d in self.devices if
                       not query or query in d.name.lower() or query in d.ip.lower()]
            self._rebuild_grid(visible)

    def closeEvent(self, event):
        """Корректно останавливаем все активные потоки перед закрытием."""
        self._timer.stop()
        if hasattr(self, '_update_checker'):
            self._update_checker.wait(2000)
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