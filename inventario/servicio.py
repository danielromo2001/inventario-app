from __future__ import annotations
import functools
import logging
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path

from . import config
from .db import conectar
from .errores import (CarritoVacio, DatosInvalidos, ErrorArchivo, ErrorBaseDatos,
                      InventarioError, ProductoDuplicado, ProductoNoEncontrado, StockInsuficiente)
from .pdf import generar_factura_pdf

log = logging.getLogger("inventario")


def _protegido(f):
    """Convierte cualquier fallo técnico (SQLite, disco) en un mensaje claro para el usuario."""
    @functools.wraps(f)
    def envoltura(self, *a, **k):
        try:
            return f(self, *a, **k)
        except InventarioError:
            raise
        except sqlite3.Error as e:
            log.exception("Error de base de datos en %s", f.__name__)
            try:
                self.con.rollback()
            except Exception:
                pass
            raise ErrorBaseDatos(
                "No se pudo completar la operación con la base de datos. Inténtalo de nuevo; "
                "si el problema continúa, cierra y vuelve a abrir la aplicación. "
                "Tus datos están protegidos por las copias de seguridad automáticas.") from e
        except OSError as e:
            log.exception("Error de archivo en %s", f.__name__)
            raise ErrorArchivo(
                f"No se pudo leer o guardar un archivo ({e.strerror or e}). Revisa que el disco "
                "tenga espacio libre y que la carpeta de la aplicación no esté protegida.") from e
    return envoltura


def _validar(nombre, precio, cantidad):
    nombre = re.sub(r"\s+", " ", (nombre or "")).strip()
    if not nombre:
        raise DatosInvalidos("El nombre del producto es obligatorio.")
    if len(nombre) > config.MAX_NOMBRE:
        raise DatosInvalidos(f"El nombre es muy largo (máximo {config.MAX_NOMBRE} caracteres).")
    if not isinstance(precio, int) or isinstance(precio, bool) or precio < 0:
        raise DatosInvalidos("El precio debe ser un número entero mayor o igual a 0.")
    if precio > config.MAX_PRECIO:
        raise DatosInvalidos(f"El precio no puede superar ${config.MAX_PRECIO:,}.".replace(",", "."))
    if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad < 0:
        raise DatosInvalidos("La cantidad debe ser un número entero mayor o igual a 0.")
    if cantidad > config.MAX_CANTIDAD:
        raise DatosInvalidos(f"La cantidad no puede superar {config.MAX_CANTIDAD:,}.".replace(",", "."))
    return nombre, precio, cantidad


class Carrito:
    """Productos que el usuario 'envía' al apartado de factura antes de confirmar la venta."""

    def __init__(self):
        self._items: dict[int, int] = {}  # producto_id -> cantidad

    def agregar(self, producto_id: int, cantidad: int = 1):
        if not isinstance(cantidad, int) or cantidad <= 0:
            raise DatosInvalidos("La cantidad a vender debe ser mayor que 0.")
        self._items[producto_id] = self._items.get(producto_id, 0) + cantidad

    def quitar(self, producto_id: int):
        self._items.pop(producto_id, None)

    def vaciar(self):
        self._items.clear()

    def items(self) -> list[tuple[int, int]]:
        return list(self._items.items())

    def __bool__(self):
        return bool(self._items)


class Inventario:
    def __init__(self, carpeta: Path | None = None):
        try:
            self.carpeta = Path(carpeta) if carpeta else config.carpeta_datos()
            self.carpeta.mkdir(parents=True, exist_ok=True)
            self.carpeta_facturas = self.carpeta / "facturas"
            self.carpeta_facturas.mkdir(exist_ok=True)
            self.carpeta_respaldos = self.carpeta / "respaldos"
            self.carpeta_respaldos.mkdir(exist_ok=True)
        except OSError as e:
            raise ErrorArchivo(f"No se pudo crear la carpeta de datos ({e.strerror or e}). "
                               "Revisa los permisos de tu usuario de Windows.") from e
        try:
            self.con = conectar(self.carpeta / "inventario.db")
            if self.con.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ErrorBaseDatos(
                    "La base de datos parece dañada. No se modificó nada. Restaura la última copia "
                    f"de seguridad desde:\n{self.carpeta_respaldos}")
        except sqlite3.Error as e:
            log.exception("No se pudo abrir la base de datos")
            raise ErrorBaseDatos(
                "No se pudo abrir la base de datos. Si otra ventana de la aplicación está abierta, "
                "ciérrala. Si el problema continúa, puedes restaurar una copia desde:\n"
                f"{self.carpeta_respaldos}") from e

    def cerrar(self):
        try:
            self.con.close()
        except sqlite3.Error:
            pass

    # ---------- Copias de seguridad ----------
    @_protegido
    def respaldar(self) -> Path | None:
        """Crea una copia diaria de la base de datos (una por día) y conserva las últimas N."""
        destino = self.carpeta_respaldos / f"inventario_{date.today():%Y-%m-%d}.db"
        if destino.exists():
            return None
        copia = sqlite3.connect(str(destino))
        try:
            self.con.backup(copia)
        finally:
            copia.close()
        for viejo in sorted(self.carpeta_respaldos.glob("inventario_*.db"))[:-config.COPIAS_A_CONSERVAR]:
            viejo.unlink(missing_ok=True)
        return destino

    # ---------- Productos (CRUD) ----------
    @_protegido
    def crear_producto(self, nombre: str, precio: int, cantidad: int) -> dict:
        nombre, precio, cantidad = _validar(nombre, precio, cantidad)
        if self.con.execute("SELECT 1 FROM productos WHERE nombre = ?", (nombre,)).fetchone():
            raise ProductoDuplicado(f"Ya existe un producto llamado «{nombre}».")
        with self.con:
            cur = self.con.execute(
                "INSERT INTO productos (nombre, precio, cantidad) VALUES (?, ?, ?)",
                (nombre, precio, cantidad))
        return self.obtener_producto(cur.lastrowid)

    @_protegido
    def obtener_producto(self, producto_id: int) -> dict:
        fila = self.con.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
        if not fila:
            raise ProductoNoEncontrado("Ese producto ya no existe en el inventario (pudo ser eliminado).")
        return dict(fila)

    @_protegido
    def listar_productos(self, buscar: str = "") -> list[dict]:
        patron = f"%{buscar.strip()}%"
        filas = self.con.execute(
            "SELECT * FROM productos WHERE nombre LIKE ? ORDER BY nombre", (patron,))
        return [dict(f) for f in filas]

    @_protegido
    def modificar_producto(self, producto_id: int, nombre: str, precio: int, cantidad: int) -> dict:
        self.obtener_producto(producto_id)
        nombre, precio, cantidad = _validar(nombre, precio, cantidad)
        if self.con.execute("SELECT 1 FROM productos WHERE nombre = ? AND id != ?",
                            (nombre, producto_id)).fetchone():
            raise ProductoDuplicado(f"Ya existe otro producto llamado «{nombre}».")
        with self.con:
            self.con.execute(
                "UPDATE productos SET nombre = ?, precio = ?, cantidad = ? WHERE id = ?",
                (nombre, precio, cantidad, producto_id))
        return self.obtener_producto(producto_id)

    @_protegido
    def eliminar_producto(self, producto_id: int) -> None:
        self.obtener_producto(producto_id)
        with self.con:  # las facturas ya emitidas conservan nombre y precio
            self.con.execute("DELETE FROM productos WHERE id = ?", (producto_id,))

    # ---------- Alertas ----------
    @_protegido
    def productos_stock_bajo(self) -> list[dict]:
        filas = self.con.execute(
            "SELECT * FROM productos WHERE cantidad <= ? ORDER BY cantidad, nombre",
            (config.UMBRAL_STOCK_BAJO,))
        return [dict(f) for f in filas]

    # ---------- Carrito / ventas ----------
    @_protegido
    def disponible_para_carrito(self, carrito: Carrito, producto_id: int) -> int:
        """Unidades que aún se pueden agregar de este producto a la factura en curso."""
        p = self.obtener_producto(producto_id)
        return max(p["cantidad"] - dict(carrito.items()).get(producto_id, 0), 0)

    @_protegido
    def agregar_al_carrito(self, carrito: Carrito, producto_id: int, cantidad: int) -> None:
        """Agrega al carrito validando contra el stock (suma lo que ya había en el carrito)."""
        if not isinstance(cantidad, int) or cantidad <= 0:
            raise DatosInvalidos("La cantidad a vender debe ser mayor que 0.")
        p = self.obtener_producto(producto_id)
        en_carrito = dict(carrito.items()).get(producto_id, 0)
        if p["cantidad"] == 0:
            raise StockInsuficiente(f"«{p['nombre']}» está agotado.")
        if en_carrito + cantidad > p["cantidad"]:
            disponible = max(p["cantidad"] - en_carrito, 0)
            raise StockInsuficiente(
                f"No hay suficiente «{p['nombre']}». Stock: {p['cantidad']}, "
                f"ya en la factura: {en_carrito}, puedes agregar máximo {disponible}.")
        carrito.agregar(producto_id, cantidad)

    @_protegido
    def validar_carrito(self, carrito: Carrito) -> list[str]:
        """Problemas actuales de la factura en curso (p. ej. el stock cambió). Vacío = todo bien."""
        problemas = []
        for pid, cant in carrito.items():
            try:
                p = self.obtener_producto(pid)
            except ProductoNoEncontrado:
                problemas.append("Un producto de la factura ya no existe en el inventario.")
                continue
            if cant > p["cantidad"]:
                problemas.append(f"«{p['nombre']}»: la factura tiene {cant} pero solo quedan {p['cantidad']}.")
        return problemas

    @_protegido
    def total_carrito(self, carrito: Carrito) -> int:
        return sum(self.obtener_producto(pid)["precio"] * cant for pid, cant in carrito.items())

    @_protegido
    def confirmar_venta(self, carrito: Carrito, cliente: str = "Cliente general") -> dict:
        """Descuenta stock, suma el total y genera el PDF. Todo o nada.

        Devuelve: {factura_id, numero, total, pdf_ruta, alertas_stock_bajo}
        """
        if not carrito:
            raise CarritoVacio("No hay productos para facturar.")
        cliente = re.sub(r"\s+", " ", (cliente or "")).strip()[:80] or "Cliente general"
        fecha = datetime.now()
        lineas, total, ruta_pdf = [], 0, None

        try:
            self.con.execute("BEGIN IMMEDIATE")
            for pid, cant in carrito.items():
                try:
                    p = self.obtener_producto(pid)
                except ProductoNoEncontrado:
                    raise ProductoNoEncontrado(
                        "Un producto de la factura fue eliminado del inventario. "
                        "Quítalo de la factura y vuelve a intentarlo.") from None
                if p["cantidad"] < cant:
                    raise StockInsuficiente(
                        f"«{p['nombre']}»: la factura tiene {cant} pero solo quedan {p['cantidad']}. "
                        "No se generó la factura; ajusta la cantidad.")
                sub = p["precio"] * cant
                total += sub
                lineas.append({"producto_id": pid, "nombre": p["nombre"],
                               "precio_unitario": p["precio"], "cantidad": cant, "subtotal": sub})
                self.con.execute("UPDATE productos SET cantidad = cantidad - ? WHERE id = ?",
                                 (cant, pid))

            cur = self.con.execute(
                "INSERT INTO facturas (fecha, cliente, total) VALUES (?, ?, ?)",
                (fecha.isoformat(timespec="seconds"), cliente, total))
            factura_id = cur.lastrowid
            numero = f"F-{factura_id:06d}"
            for ln in lineas:
                self.con.execute(
                    "INSERT INTO factura_items (factura_id, producto_id, nombre, precio_unitario,"
                    " cantidad, subtotal) VALUES (?, ?, ?, ?, ?, ?)",
                    (factura_id, ln["producto_id"], ln["nombre"], ln["precio_unitario"],
                     ln["cantidad"], ln["subtotal"]))

            nombre_cliente = re.sub(r"[^\w\-]+", "_", cliente)[:30]
            ruta_pdf = self.carpeta_facturas / f"{numero}_{nombre_cliente}.pdf"
            try:
                generar_factura_pdf(ruta_pdf, config.NOMBRE_NEGOCIO, numero,
                                    fecha.strftime("%d/%m/%Y %H:%M"), cliente, lineas, total,
                                    config.DIRECCION_NEGOCIO, config.TELEFONO_NEGOCIO,
                                    config.RUTA_LOGO)
            except Exception as e:
                log.exception("Falló la creación del PDF")
                raise ErrorArchivo(
                    "No se pudo crear el PDF de la factura, así que la venta NO se registró y el "
                    f"inventario no cambió. Revisa el espacio en disco. Detalle: {e}") from e
            self.con.execute("UPDATE facturas SET numero = ?, pdf_ruta = ? WHERE id = ?",
                             (numero, str(ruta_pdf), factura_id))
            self.con.commit()
        except BaseException:
            try:
                self.con.rollback()
            except sqlite3.Error:
                pass
            if ruta_pdf is not None:
                try:
                    ruta_pdf.unlink(missing_ok=True)  # no dejar PDFs de ventas que no existen
                except OSError:
                    pass
            raise

        carrito.vaciar()
        ids = [ln["producto_id"] for ln in lineas]
        try:
            alertas = [p for p in self.productos_stock_bajo() if p["id"] in ids]
        except InventarioError:
            alertas = []  # la venta ya quedó registrada; la alerta es un extra
        return {"factura_id": factura_id, "numero": numero, "total": total,
                "pdf_ruta": str(ruta_pdf), "alertas_stock_bajo": alertas}

    @_protegido
    def listar_facturas(self) -> list[dict]:
        return [dict(f) for f in self.con.execute(
            "SELECT id, numero, fecha, cliente, total, pdf_ruta FROM facturas ORDER BY id DESC")]
