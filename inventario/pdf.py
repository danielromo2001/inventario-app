from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

NARANJA = colors.HexColor("#C8631E")
OSCURO = colors.HexColor("#222222")
GRIS = colors.HexColor("#777777")
LINEA = colors.HexColor("#E3DDD2")

_FUENTES = Path(__file__).parent / "assets" / "fonts"
_registradas = False


def _registrar_fuentes():
    """Poppins va empacada con la app: el PDF se ve igual en cualquier computador."""
    global _registradas
    if _registradas:
        return
    for nombre in ("Light", "Regular", "Medium", "Bold"):
        pdfmetrics.registerFont(TTFont(f"Poppins-{nombre}", str(_FUENTES / f"Poppins-{nombre}.ttf")))
    _registradas = True


def pesos(valor: int) -> str:
    return "$ " + f"{valor:,}".replace(",", ".")


def generar_factura_pdf(ruta: Path, negocio: str, numero: str, fecha: str,
                        cliente: str, items: list[dict], total: int,
                        direccion: str = "", telefono: str = "", logo: Path | None = None) -> None:
    _registrar_fuentes()
    ancho, alto = A4
    M = 18 * mm  # margen lateral
    hay_logo = bool(logo and Path(logo).exists())

    celda = ParagraphStyle("celda", fontName="Poppins-Regular", fontSize=11, leading=14.5,
                           textColor=OSCURO)
    cliente_est = ParagraphStyle("cli", fontName="Poppins-Medium", fontSize=14, leading=18,
                                 textColor=OSCURO)
    etiqueta = ParagraphStyle("eti", fontName="Poppins-Regular", fontSize=9, leading=12,
                              textColor=GRIS)

    def pie(c, _doc):
        c.saveState()
        c.setStrokeColor(LINEA)
        c.setLineWidth(0.8)
        c.line(M, 22 * mm, ancho - M, 22 * mm)
        c.setFillColor(OSCURO)
        c.setFont("Poppins-Medium", 10.5)
        c.drawCentredString(ancho / 2, 15 * mm, "Gracias por su compra")
        c.setFillColor(GRIS)
        c.setFont("Poppins-Light", 9)
        c.drawCentredString(ancho / 2, 10 * mm, f"{negocio}  ·  {direccion}  ·  Tel: {telefono}")
        c.restoreState()

    def primera(c, doc):
        c.saveState()
        top = alto - 16 * mm
        if hay_logo:
            iw, ih = ImageReader(str(logo)).getSize()
            w = 50 * mm
            h = w * ih / iw
            c.drawImage(str(logo), M, top - h, width=w, height=h, mask="auto")
            base = top - h
        else:
            c.setFillColor(OSCURO)
            c.setFont("Poppins-Bold", 20)
            c.drawString(M, top - 8 * mm, negocio)
            base = top - 14 * mm
        x = ancho - M
        c.setFillColor(GRIS)
        c.setFont("Poppins-Medium", 10)
        c.drawRightString(x, top - 4 * mm, "FACTURA DE VENTA")
        c.setFillColor(OSCURO)
        c.setFont("Poppins-Bold", 26)
        c.drawRightString(x, top - 15 * mm, numero)
        c.setFillColor(GRIS)
        c.setFont("Poppins-Regular", 11)
        c.drawRightString(x, top - 23 * mm, fecha)
        c.setStrokeColor(NARANJA)
        c.setLineWidth(1.4)
        c.line(M, base - 6 * mm, ancho - M, base - 6 * mm)
        c.restoreState()
        pie(c, doc)

    doc = SimpleDocTemplate(str(ruta), pagesize=A4, leftMargin=M, rightMargin=M,
                            topMargin=16 * mm, bottomMargin=30 * mm, title=f"Factura {numero}",
                            author=negocio)

    espacio_cabecera = 30 * mm
    historia = [Spacer(1, espacio_cabecera + 12 * mm),
                Paragraph("CLIENTE", etiqueta),
                Paragraph(cliente, cliente_est),
                Spacer(1, 9 * mm)]

    filas = [["PRODUCTO", "CANT.", "PRECIO UNIT.", "SUBTOTAL"]]
    for it in items:
        filas.append([Paragraph(it["nombre"], celda), str(it["cantidad"]),
                      pesos(it["precio_unitario"]), pesos(it["subtotal"])])
    util = ancho - 2 * M
    tabla = Table(filas, colWidths=[util - 95 * mm, 18 * mm, 38 * mm, 39 * mm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Poppins-Medium"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), GRIS),
        ("FONTNAME", (0, 1), (-1, -1), "Poppins-Regular"),
        ("FONTSIZE", (0, 1), (-1, -1), 11),
        ("TEXTCOLOR", (0, 1), (-1, -1), OSCURO),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (0, -1), 0), ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, OSCURO),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINEA),
    ]))

    unidades = sum(it["cantidad"] for it in items)
    caja = Table([["Unidades", str(unidades)], ["TOTAL A PAGAR", pesos(total)]],
                 colWidths=[58 * mm, 48 * mm], hAlign="RIGHT")
    caja.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Poppins-Regular"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("TEXTCOLOR", (0, 0), (-1, 0), GRIS),
        ("FONTNAME", (0, 1), (-1, 1), "Poppins-Bold"),
        ("FONTSIZE", (0, 1), (0, 1), 11),
        ("FONTSIZE", (1, 1), (1, 1), 16),
        ("TEXTCOLOR", (0, 1), (0, 1), OSCURO),
        ("TEXTCOLOR", (1, 1), (1, 1), NARANJA),
        ("LINEABOVE", (0, 1), (-1, 1), 1.4, NARANJA),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
    ]))
    historia += [tabla, Spacer(1, 8 * mm), caja]
    doc.build(historia, onFirstPage=primera, onLaterPages=pie)
