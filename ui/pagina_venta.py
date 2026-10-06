from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QDesktopServices
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget)

from inventario import Carrito, InventarioError, ProductoNoEncontrado, config
from inventario.pdf import pesos
from .estilos import ROJO_TEXTO, celda, crear_tabla
from .seguro import seguro


class PaginaVenta(QWidget):
    venta_realizada = Signal()

    def __init__(self, inv):
        super().__init__()
        self.inv = inv
        self.carrito = Carrito()

        titulo = QLabel("Nueva venta"); titulo.setObjectName("titulo")
        self.aviso = QLabel(); self.aviso.setObjectName("aviso"); self.aviso.setWordWrap(True)
        self.aviso.hide()

        # --- Izquierda: catálogo ---
        self.buscar = QLineEdit(); self.buscar.setPlaceholderText("Buscar producto...")
        self.buscar.setClearButtonEnabled(True)
        self.buscar.textChanged.connect(self._cargar_catalogo)
        self.catalogo = crear_tabla(["Producto", "Precio", "Disponibles"], derecha=(1, 2))
        self.catalogo.doubleClicked.connect(self._agregar)
        self.catalogo.itemSelectionChanged.connect(self._actualizar_disponible)
        self.cant = QSpinBox(); self.cant.setRange(1, config.MAX_CANTIDAD); self.cant.setValue(1)
        self.cant.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.cant.setFixedWidth(90)
        self.cant.lineEdit().returnPressed.connect(self._agregar)  # Enter agrega
        self.lbl_disp = QLabel(); self.lbl_disp.setObjectName("subtitulo")
        self.b_agregar = QPushButton("Agregar a la factura  →"); self.b_agregar.setObjectName("primario")
        self.b_agregar.clicked.connect(self._agregar)
        fila_agregar = QHBoxLayout()
        fila_agregar.addWidget(QLabel("Cantidad:")); fila_agregar.addWidget(self.cant)
        fila_agregar.addWidget(self.b_agregar, 1)

        izq = QVBoxLayout()
        izq.addWidget(self.buscar); izq.addWidget(self.catalogo, 1)
        izq.addWidget(self.lbl_disp); izq.addLayout(fila_agregar)

        # --- Derecha: factura ---
        sub = QLabel("Factura en curso"); sub.setObjectName("subtitulo")
        self.cliente = QLineEdit(); self.cliente.setPlaceholderText("Nombre del cliente (opcional)")
        self.cliente.setMaxLength(80)
        self.tabla_carrito = crear_tabla(["Producto", "Cant.", "Subtotal"], derecha=(1, 2))
        b_quitar = QPushButton("Quitar seleccionado"); b_quitar.clicked.connect(self._quitar)
        b_vaciar = QPushButton("Vaciar"); b_vaciar.clicked.connect(self._vaciar)
        fila_q = QHBoxLayout(); fila_q.addWidget(b_quitar); fila_q.addWidget(b_vaciar)
        self.total = QLabel(pesos(0)); self.total.setObjectName("total")
        self.total.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.b_generar = QPushButton("Generar factura PDF"); self.b_generar.setObjectName("primario")
        self.b_generar.clicked.connect(self._confirmar)

        der = QVBoxLayout()
        der.addWidget(sub); der.addWidget(self.cliente); der.addWidget(self.tabla_carrito, 1)
        der.addLayout(fila_q)
        fila_total = QHBoxLayout(); fila_total.addWidget(QLabel("TOTAL")); fila_total.addWidget(self.total, 1)
        der.addLayout(fila_total); der.addWidget(self.b_generar)

        cuerpo = QHBoxLayout(); cuerpo.setSpacing(24)
        cuerpo.addLayout(izq, 1); cuerpo.addLayout(der, 1)

        capa = QVBoxLayout(self)
        capa.setContentsMargins(32, 28, 32, 28); capa.setSpacing(14)
        capa.addWidget(titulo); capa.addWidget(self.aviso); capa.addLayout(cuerpo, 1)

    def hay_pendiente(self) -> bool:
        return bool(self.carrito)

    # ---------- catálogo ----------
    @seguro
    def refrescar(self, *_):
        self._cargar_catalogo()
        self._cargar_carrito()

    def _pid_catalogo(self):
        fila = self.catalogo.currentRow()
        return self.catalogo.item(fila, 0).data(Qt.ItemDataRole.UserRole) if fila >= 0 else None

    @seguro
    def _cargar_catalogo(self, *_):
        previo = self._pid_catalogo()
        productos = self.inv.listar_productos(self.buscar.text())
        self.catalogo.setRowCount(len(productos))
        gris = QBrush(QColor("#AAAAAA"))
        for fila, p in enumerate(productos):
            agotado = p["cantidad"] == 0
            celdas = [celda(p["nombre"], dato=p["id"]), celda(pesos(p["precio"]), True),
                      celda("Agotado" if agotado else p["cantidad"], True)]
            for col, it in enumerate(celdas):
                if agotado:
                    it.setForeground(gris)
                self.catalogo.setItem(fila, col, it)
            if previo is not None and p["id"] == previo:
                self.catalogo.selectRow(fila)
        self._actualizar_disponible()

    @seguro
    def _actualizar_disponible(self, *_):
        """Limita la cantidad a lo que realmente se puede agregar y lo dice con claridad."""
        pid = self._pid_catalogo()
        if pid is None:
            self.lbl_disp.setText("Selecciona un producto de la lista.")
            self.cant.setRange(1, config.MAX_CANTIDAD)
            self.b_agregar.setEnabled(True)
            return
        try:
            disp = self.inv.disponible_para_carrito(self.carrito, pid)
        except ProductoNoEncontrado:
            self._cargar_catalogo()
            return
        self.cant.setRange(1, max(disp, 1))
        self.b_agregar.setEnabled(disp > 0)
        self.lbl_disp.setText(f"Puedes agregar hasta {disp} unidad(es)." if disp > 0 else
                              "Sin unidades disponibles para agregar.")

    @seguro
    def _agregar(self, *_):
        pid = self._pid_catalogo()
        if pid is None:
            QMessageBox.information(self, "Selecciona un producto",
                                    "Haz clic sobre un producto del catálogo y luego en «Agregar».")
            return
        try:
            self.inv.agregar_al_carrito(self.carrito, pid, self.cant.value())
        except InventarioError as e:
            QMessageBox.warning(self, "No se pudo agregar", str(e))
            self._actualizar_disponible()
            return
        self.cant.setValue(1)
        self._cargar_carrito()
        self._actualizar_disponible()

    # ---------- factura en curso ----------
    def _cargar_carrito(self):
        filas, quitados = [], False
        for pid, cant in self.carrito.items():
            try:
                filas.append((self.inv.obtener_producto(pid), cant))
            except ProductoNoEncontrado:
                self.carrito.quitar(pid)  # lo eliminaron del inventario mientras tanto
                quitados = True
        problemas = self.inv.validar_carrito(self.carrito)

        self.tabla_carrito.setRowCount(len(filas))
        rojo = QBrush(QColor(ROJO_TEXTO))
        for i, (p, cant) in enumerate(filas):
            celdas = [celda(p["nombre"], dato=p["id"]), celda(cant, True),
                      celda(pesos(p["precio"] * cant), True)]
            for col, it in enumerate(celdas):
                if cant > p["cantidad"]:
                    it.setForeground(rojo)
                self.tabla_carrito.setItem(i, col, it)
        self.total.setText(pesos(self.inv.total_carrito(self.carrito)))

        mensajes = list(problemas)
        if quitados:
            mensajes.append("Se quitó de la factura un producto que fue eliminado del inventario.")
        if mensajes:
            if problemas:
                mensajes.append("Quita o ajusta esas líneas para poder generar la factura.")
            self.aviso.setText("⚠  " + "\n".join(mensajes)); self.aviso.show()
        else:
            self.aviso.hide()
        self.b_generar.setEnabled(bool(self.carrito) and not problemas)

    @seguro
    def _quitar(self, *_):
        fila = self.tabla_carrito.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Selecciona una línea",
                                    "Haz clic sobre el producto de la factura que quieres quitar.")
            return
        self.carrito.quitar(self.tabla_carrito.item(fila, 0).data(Qt.ItemDataRole.UserRole))
        self._cargar_carrito(); self._actualizar_disponible()

    @seguro
    def _vaciar(self, *_):
        self.carrito.vaciar()
        self._cargar_carrito(); self._actualizar_disponible()

    @seguro
    def _confirmar(self, *_):
        if not self.carrito:
            return
        self.b_generar.setEnabled(False)  # evita doble clic = doble venta
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resultado, error = None, ""
        try:
            resultado = self.inv.confirmar_venta(self.carrito, self.cliente.text())
        except InventarioError as e:
            error = str(e)
        finally:
            QApplication.restoreOverrideCursor()
        if resultado is None:
            QMessageBox.warning(self, "No se generó la factura", error)
            self.refrescar()
            return

        self.cliente.clear()
        self.refrescar()
        mensaje = f"Factura {resultado['numero']} generada por {pesos(resultado['total'])}."
        if resultado["alertas_stock_bajo"]:
            lista = "\n".join(f"• {p['nombre']}: quedan {p['cantidad']}"
                              for p in resultado["alertas_stock_bajo"])
            mensaje += f"\n\n⚠ Stock bajo:\n{lista}"
        abierto = QDesktopServices.openUrl(QUrl.fromLocalFile(resultado["pdf_ruta"]))
        if not abierto:
            mensaje += ("\n\nNo pude abrir el PDF automáticamente (¿hay un lector de PDF instalado?)."
                        f"\nLo encuentras en:\n{resultado['pdf_ruta']}")
        QMessageBox.information(self, "Venta registrada", mensaje)
        self.venta_realizada.emit()
