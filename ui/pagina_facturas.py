from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from inventario.pdf import pesos
from .estilos import celda, crear_tabla
from .seguro import seguro


class PaginaFacturas(QWidget):
    def __init__(self, inv):
        super().__init__()
        self.inv = inv
        titulo = QLabel("Facturas emitidas"); titulo.setObjectName("titulo")
        self.tabla = crear_tabla(["Cliente", "Número", "Fecha", "Total"], derecha=(3,))
        self.tabla.doubleClicked.connect(self._abrir)
        self.vacio = QLabel("Aún no has generado facturas.\nCuando hagas una venta aparecerá aquí.")
        self.vacio.setObjectName("subtitulo"); self.vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.boton = QPushButton("Abrir PDF"); self.boton.setObjectName("primario")
        self.boton.clicked.connect(self._abrir)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(32, 28, 32, 28); capa.setSpacing(14)
        capa.addWidget(titulo); capa.addWidget(self.tabla, 1); capa.addWidget(self.vacio)
        capa.addWidget(self.boton)

    @seguro
    def refrescar(self, *_):
        facturas = self.inv.listar_facturas()
        self.tabla.setRowCount(len(facturas))
        for i, f in enumerate(facturas):
            try:
                fecha = datetime.fromisoformat(f["fecha"]).strftime("%d/%m/%Y %H:%M")
            except (TypeError, ValueError):
                fecha = str(f["fecha"])
            self.tabla.setItem(i, 0, celda(f["cliente"], dato=f["pdf_ruta"]))
            self.tabla.setItem(i, 1, celda(f["numero"] or ""))
            self.tabla.setItem(i, 2, celda(fecha))
            self.tabla.setItem(i, 3, celda(pesos(f["total"]), True))
        self.tabla.setVisible(bool(facturas))
        self.vacio.setVisible(not facturas)
        self.boton.setEnabled(bool(facturas))

    @seguro
    def _abrir(self, *_):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Selecciona una factura",
                                    "Haz clic sobre una factura de la lista.")
            return
        ruta = self.tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole)
        if not ruta or not Path(ruta).exists():
            QMessageBox.warning(self, "No encuentro el PDF",
                                "El archivo de esta factura ya no está en su ubicación "
                                f"(se movió o se borró):\n{ruta}\n\nLos datos de la venta siguen guardados.")
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(ruta)):
            QMessageBox.warning(self, "No se pudo abrir",
                                f"No pude abrir el PDF automáticamente. Búscalo en:\n{ruta}")
