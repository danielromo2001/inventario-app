from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
                               QVBoxLayout, QWidget)

from inventario import InventarioError, config
from inventario.pdf import pesos
from .dialogos import DialogoProducto
from .estilos import ROJO_FONDO, ROJO_TEXTO, celda, crear_tabla
from .seguro import preguntar, seguro


class PaginaInventario(QWidget):
    datos_cambiados = Signal()

    def __init__(self, inv):
        super().__init__()
        self.inv = inv

        titulo = QLabel("Inventario"); titulo.setObjectName("titulo")
        self.aviso = QLabel(); self.aviso.setObjectName("aviso"); self.aviso.hide()

        self.buscar = QLineEdit(); self.buscar.setPlaceholderText("Buscar producto...")
        self.buscar.setClearButtonEnabled(True)
        self.buscar.textChanged.connect(self.refrescar)
        b_nuevo = QPushButton("+ Nuevo producto"); b_nuevo.setObjectName("primario")
        b_editar = QPushButton("Modificar")
        b_borrar = QPushButton("Eliminar"); b_borrar.setObjectName("peligro")
        b_nuevo.clicked.connect(self._nuevo)
        b_editar.clicked.connect(self._editar)
        b_borrar.clicked.connect(self._eliminar)

        barra = QHBoxLayout()
        barra.addWidget(self.buscar, 1)
        for b in (b_nuevo, b_editar, b_borrar):
            barra.addWidget(b)

        self.tabla = crear_tabla(["Producto", "Precio", "Cantidad", "Estado"], derecha=(1, 2))
        self.tabla.doubleClicked.connect(self._editar)
        self.vacio = QLabel(); self.vacio.setObjectName("subtitulo")
        self.vacio.setAlignment(Qt.AlignmentFlag.AlignCenter); self.vacio.setWordWrap(True)

        capa = QVBoxLayout(self)
        capa.setContentsMargins(32, 28, 32, 28)
        capa.setSpacing(14)
        capa.addWidget(titulo)
        capa.addWidget(self.aviso)
        capa.addLayout(barra)
        capa.addWidget(self.tabla, 1)
        capa.addWidget(self.vacio)

    def _id_actual(self):
        fila = self.tabla.currentRow()
        return self.tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole) if fila >= 0 else None

    @seguro
    def refrescar(self, *_):
        self._llenar(self._id_actual())

    def _llenar(self, seleccionar_id=None):
        texto = self.buscar.text().strip()
        productos = self.inv.listar_productos(texto)
        self.tabla.setRowCount(len(productos))
        for fila, p in enumerate(productos):
            bajo = p["cantidad"] <= config.UMBRAL_STOCK_BAJO
            estado = "Agotado" if p["cantidad"] == 0 else ("Stock bajo" if bajo else "OK")
            celdas = [celda(p["nombre"], dato=p["id"]), celda(pesos(p["precio"]), True),
                      celda(p["cantidad"], True), celda(estado)]
            for col, it in enumerate(celdas):
                if bajo:
                    it.setBackground(QBrush(QColor(ROJO_FONDO)))
                    it.setForeground(QBrush(QColor(ROJO_TEXTO)))
                self.tabla.setItem(fila, col, it)
            if seleccionar_id is not None and p["id"] == seleccionar_id:
                self.tabla.selectRow(fila)
        if not productos:
            self.vacio.setText(f"No hay productos que coincidan con «{texto}»." if texto else
                               "Aún no tienes productos.\nPresiona «+ Nuevo producto» para agregar el primero.")
        self.vacio.setVisible(not productos)
        self.tabla.setVisible(bool(productos))
        bajos = self.inv.productos_stock_bajo()
        if bajos:
            self.aviso.setText(f"⚠  {len(bajos)} producto(s) con {config.UMBRAL_STOCK_BAJO} "
                               "unidades o menos. Es hora de reponer.")
            self.aviso.show()
        else:
            self.aviso.hide()

    def _id_seleccionado(self):
        pid = self._id_actual()
        if pid is None:
            QMessageBox.information(self, "Selecciona un producto",
                                    "Primero haz clic sobre un producto de la lista.")
        return pid

    @seguro
    def _nuevo(self, *_):
        dlg = DialogoProducto(self)
        while dlg.exec():
            try:
                creado = self.inv.crear_producto(*dlg.datos())
            except Exception as e:
                if not isinstance(e, InventarioError):
                    raise
                QMessageBox.warning(self, "No se pudo guardar", str(e))
                continue  # el formulario se reabre con lo que escribió
            self.buscar.clear()
            self._llenar(creado["id"]); self.datos_cambiados.emit()
            break

    @seguro
    def _editar(self, *_):
        pid = self._id_seleccionado()
        if pid is None:
            return
        dlg = DialogoProducto(self, self.inv.obtener_producto(pid))
        while dlg.exec():
            try:
                self.inv.modificar_producto(pid, *dlg.datos())
            except Exception as e:
                if not isinstance(e, InventarioError):
                    raise
                QMessageBox.warning(self, "No se pudo guardar", str(e))
                continue
            self._llenar(pid); self.datos_cambiados.emit()
            break

    @seguro
    def _eliminar(self, *_):
        pid = self._id_seleccionado()
        if pid is None:
            return
        p = self.inv.obtener_producto(pid)
        extra = f"\nTiene {p['cantidad']} unidad(es) en inventario." if p["cantidad"] else ""
        if preguntar(self, "Eliminar producto",
                     f"¿Eliminar «{p['nombre']}»?{extra}\nLas facturas ya emitidas no cambian.",
                     si="Sí, eliminar", no="No, conservar"):
            self.inv.eliminar_producto(pid)
            self._llenar(); self.datos_cambiados.emit()
