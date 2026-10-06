from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

ASSETS = Path(__file__).resolve().parent.parent / "inventario" / "assets"
NARANJA = "#C8631E"
ROJO_FONDO = "#FBE3E0"
ROJO_TEXTO = "#B3261E"


def cargar_fuente(app) -> None:
    for ttf in (ASSETS / "fonts").glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(ttf))
    app.setFont(QFont("Poppins", 10))


QSS = f"""
QWidget {{ color: #222222; font-size: 10.5pt; }}
#contenido, QDialog {{ background: #FAF8F4; }}
#barra {{ background: #FFFFFF; border-right: 1px solid #E3DDD2; }}
#titulo {{ font-size: 20pt; font-weight: 700; }}
#subtitulo {{ color: #777777; }}
#aviso {{ background: {ROJO_FONDO}; color: {ROJO_TEXTO}; border-radius: 8px; padding: 10px 14px; font-weight: 600; }}
#total {{ font-size: 22pt; font-weight: 700; color: {NARANJA}; }}

QPushButton {{ background: #FFFFFF; border: 1px solid #D8D0BB; border-radius: 8px; padding: 9px 18px; }}
QPushButton:hover {{ background: #F3EEE3; }}
QPushButton:disabled {{ color: #AAAAAA; }}
QPushButton#primario {{ background: {NARANJA}; color: white; border: none; font-weight: 600; }}
QPushButton#primario:hover {{ background: #AD5217; }}
QPushButton#peligro {{ color: {ROJO_TEXTO}; border-color: #E5B5B0; }}
QPushButton#nav {{ text-align: left; border: none; border-radius: 8px; padding: 12px 16px; background: transparent; font-weight: 500; }}
QPushButton#nav:hover {{ background: #F3EEE3; }}
QPushButton#nav:checked {{ background: {NARANJA}; color: white; }}

QLineEdit, QSpinBox {{ background: white; border: 1px solid #D8D0BB; border-radius: 8px; padding: 8px 10px; }}
QLineEdit:focus, QSpinBox:focus {{ border: 1px solid {NARANJA}; }}

QTableWidget {{ background: white; alternate-background-color: #FAF8F4; border: 1px solid #E3DDD2;
                border-radius: 8px; outline: 0; }}
QTableWidget::item {{ border: none; padding: 0px 10px; }}
QTableWidget::item:selected, QTableWidget::item:selected:active, QTableWidget::item:selected:!active
    {{ background: {NARANJA}; color: #FFFFFF; }}
QHeaderView::section {{ background: white; color: #777777; border: none; border-bottom: 1.5px solid #222222;
                        padding: 10px 10px; font-weight: 500; }}
"""


def crear_tabla(columnas: list[str], derecha: tuple[int, ...] = ()) -> QTableWidget:
    """derecha: índices de columnas numéricas (encabezado y valores alineados a la derecha)."""
    t = QTableWidget(0, len(columnas))
    t.setHorizontalHeaderLabels(columnas)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    t.setAlternatingRowColors(True)
    t.setShowGrid(False)
    t.verticalHeader().setVisible(False)
    t.verticalHeader().setDefaultSectionSize(42)
    for i in range(len(columnas)):
        alin = Qt.AlignmentFlag.AlignRight if i in derecha else Qt.AlignmentFlag.AlignLeft
        t.horizontalHeaderItem(i).setTextAlignment(alin | Qt.AlignmentFlag.AlignVCenter)
    cab = t.horizontalHeader()
    cab.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    for i in range(1, len(columnas)):
        cab.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
    return t


def celda(texto, derecha: bool = False, dato=None) -> QTableWidgetItem:
    it = QTableWidgetItem(str(texto))
    if derecha:
        it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    if dato is not None:
        it.setData(Qt.ItemDataRole.UserRole, dato)
    return it
