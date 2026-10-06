"""Pruebas de robustez: python prueba_errores.py"""
import tempfile
from pathlib import Path
import inventario.servicio as srv
from inventario import *

inv = Inventario(tempfile.mkdtemp())
a = inv.crear_producto("Aceite 20W-50", 30000, 5)

# 1) Validaciones de datos
for args in [("", 1, 1), ("x" * 500, 1, 1), ("ok", -1, 1), ("ok", 1, -1), ("ok", 10**12, 1), ("ok", 1.5, 1), ("ok", True, 1)]:
    try: inv.crear_producto(*args); raise SystemExit(f"FALLO: aceptó {args[1:]}")
    except DatosInvalidos as e: print("OK dato inválido:", e)

# 2) Carrito y stock cambiante
c = Carrito(); inv.agregar_al_carrito(c, a["id"], 4)
print("Disponible para agregar:", inv.disponible_para_carrito(c, a["id"]))
inv.modificar_producto(a["id"], "Aceite 20W-50", 30000, 2)
print("Problemas en carrito:", inv.validar_carrito(c))
try: inv.confirmar_venta(c); raise SystemExit("FALLO: vendió sin stock")
except StockInsuficiente as e: print("OK confirmar bloqueado:", e)

# 3) Falla al crear el PDF: no debe quedar nada a medias
real = srv.generar_factura_pdf
def falla(ruta, *a, **k):
    Path(ruta).write_bytes(b"%PDF parcial"); raise PermissionError("disco lleno")
srv.generar_factura_pdf = falla
c2 = Carrito(); inv.agregar_al_carrito(c2, a["id"], 2)
try: inv.confirmar_venta(c2); raise SystemExit("FALLO: no avisó del PDF")
except ErrorArchivo as e: print("OK fallo PDF:", str(e)[:80], "...")
assert inv.obtener_producto(a["id"])["cantidad"] == 2, "el stock cambió"
assert inv.listar_facturas() == [], "quedó una factura fantasma"
assert not list(inv.carpeta_facturas.glob("*.pdf")), "quedó un PDF a medias"
srv.generar_factura_pdf = real
r = inv.confirmar_venta(c2, "  Ana   María  "); print("OK venta tras recuperarse:", r["numero"])

# 4) Producto eliminado con la factura abierta
b = inv.crear_producto("Filtro", 10000, 3)
c3 = Carrito(); inv.agregar_al_carrito(c3, b["id"], 1); inv.eliminar_producto(b["id"])
try: inv.confirmar_venta(c3)
except ProductoNoEncontrado as e: print("OK producto eliminado:", e)

# 5) Copia de seguridad
print("Respaldo:", inv.respaldar() is not None, "| segundo intento mismo día:", inv.respaldar())

# 6) Base de datos caída: mensaje claro, no excepción técnica
inv.con.close()
try: inv.listar_productos(); raise SystemExit("FALLO")
except ErrorBaseDatos as e: print("OK base de datos:", str(e)[:70], "...")
print("TODO OK")
