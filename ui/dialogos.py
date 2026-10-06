from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractSpinBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
                               QMessageBox, QSpinBox, QVBoxLayout)

from inventario import config
from .seguro import preguntar


class DialogoProducto(QDialog):
    """Formulario para crear o modificar un producto."""

    def __init__(self, parent=None, producto: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Modificar producto" if producto else "Nuevo producto")
        self.setMinimumWidth(420)

        self.nombre = QLineEdit()
        self.nombre.setMaxLength(config.MAX_NOMBRE)
        self.nombre.setPlaceholderText("Ej: Aceite 20W-50 Carro 1L")
        self.precio = QSpinBox()
        self.precio.setRange(0, config.MAX_PRECIO)
        self.precio.setPrefix("$ ")
        self.cantidad = QSpinBox()
        self.cantidad.setRange(0, config.MAX_CANTIDAD)
        for campo in (self.precio, self.cantidad):
            campo.setGroupSeparatorShown(True)
            campo.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            campo.setAlignment(Qt.AlignmentFlag.AlignLeft)
            campo.setKeyboardTracking(False)

        if producto:
            self.nombre.setText(producto["nombre"])
            self.precio.setValue(producto["precio"])
            self.cantidad.setValue(producto["cantidad"])

        form = QFormLayout()
        form.addRow("Nombre", self.nombre)
        form.addRow("Precio", self.precio)
        form.addRow("Cantidad", self.cantidad)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        guardar = botones.button(QDialogButtonBox.StandardButton.Save)
        guardar.setText("Guardar"); guardar.setObjectName("primario"); guardar.setDefault(True)
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)

        capa = QVBoxLayout(self)
        capa.setContentsMargins(24, 24, 24, 24)
        capa.setSpacing(18)
        capa.addLayout(form)
        capa.addWidget(botones)
        self.nombre.setFocus()

    def accept(self):
        """Revisa lo evidente antes de cerrar, para que el usuario corrija sin perder lo escrito."""
        nombre, precio, _ = self.datos()
        if not nombre:
            QMessageBox.information(self, "Falta el nombre", "Escribe el nombre del producto.")
            self.nombre.setFocus()
            return
        if precio == 0 and not preguntar(
                self, "Precio en $0",
                "El precio quedó en $ 0. ¿Seguro que quieres guardarlo así?",
                si="Sí, guardar", no="No, corregir"):
            self.precio.setFocus(); self.precio.selectAll()
            return
        super().accept()

    def datos(self) -> tuple[str, int, int]:
        return self.nombre.text().strip(), self.precio.value(), self.cantidad.value()
