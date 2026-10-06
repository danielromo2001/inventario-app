<div align="center">
  <img src="inventario/assets/logo_marca.png" alt="ROMO El Rincón del Lubricante" width="380">

  # ROMO Inventario

  **Aplicación de escritorio para administrar productos, controlar existencias y generar facturas en PDF.**

  ![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
  ![PySide6](https://img.shields.io/badge/Interfaz-PySide6-41CD52?logo=qt&logoColor=white)
  ![SQLite](https://img.shields.io/badge/Base_de_datos-SQLite-003B57?logo=sqlite&logoColor=white)
</div>

---

## Acerca del proyecto

ROMO Inventario es una aplicación de escritorio pensada para facilitar las tareas diarias de un negocio: mantener el catálogo de productos, revisar las existencias y registrar ventas con su factura correspondiente.

## Funcionalidades

- **Inventario de productos:** crea, busca, modifica y elimina productos; administra precios y cantidades.
- **Alertas de existencias:** identifica productos agotados y avisa cuando quedan 3 unidades o menos.
- **Registro de ventas:** arma una factura con los productos disponibles y el nombre opcional del cliente.
- **Facturas en PDF:** registra la venta y descuenta las existencias al generar la factura. Puedes volver a abrir los PDF desde la lista de facturas emitidas.
- **Datos protegidos:** guarda la información en una base de datos SQLite local y crea respaldos diarios, conservando hasta 15.

## Requisitos

- Windows
- Python 3.10 o superior
- Git

## Instalación y ejecución

Abre PowerShell y ejecuta:

```powershell
git clone https://github.com/danielromo2001/inventario-app.git
cd inventario-app

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Si PowerShell no reconoce `py`, instala Python desde [python.org](https://www.python.org/downloads/) y asegúrate de habilitar la opción para añadirlo al `PATH`.

Para salir del entorno virtual:

```powershell
deactivate
```

## Pruebas

Con el entorno virtual activado y las dependencias instaladas:

```powershell
python prueba_backend.py
python prueba_errores.py
```

## Datos y respaldos

La base de datos, las facturas y los respaldos se guardan localmente en:

```text
%LOCALAPPDATA%\InventarioLubricantes\
```

La aplicación crea automáticamente las carpetas `facturas` y `respaldos`. Para evitar conflictos con la base de datos, solo se permite abrir una instancia a la vez. Se recomienda conservar copias de los respaldos fuera del equipo.

## Tecnologías

- [Python](https://www.python.org/)
- [PySide6](https://doc.qt.io/qtforpython-6/)
- [SQLite](https://www.sqlite.org/)
- [ReportLab](https://www.reportlab.com/dev/docs/)

---

<div align="center">
  Hecho para <strong>ROMO El Rincón del Lubricante</strong>
</div>
