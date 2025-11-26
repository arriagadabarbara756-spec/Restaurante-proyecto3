# boleta.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

class Boleta:
    """
    Genera un PDF de boleta a partir de una lista de items:
    Cada item debe ser: (nombre, cantidad, precio_unitario, subtotal)
    """

    def __init__(self, items, fecha=None):
        self.items = items
        self.fecha = fecha

    def generar_pdf(self, salida="boleta.pdf"):
        doc = SimpleDocTemplate(
            salida, pagesize=letter,
            leftMargin=36, rightMargin=36,
            topMargin=36, bottomMargin=36
        )

        styles = getSampleStyleSheet()
        story = []

        # ----------------- HEADER -----------------
        empresa = Paragraph(
            "<b>Boleta Restaurante</b><br/>"
            "Restaurante Crunch<br/>"
            "RUT: 12.345.678-9<br/>"
            "Dirección: Calle Ejemplo 123, Temuco<br/>"
            "Teléfono: +56 9 1234 5678",
            styles["Normal"]
        )

        if self.fecha is not None:
            fecha_val = self.fecha.strftime("%d/%m/%Y %H:%M")
        else:
            fecha_val = datetime.now().strftime("%d/%m/%Y %H:%M")
        fecha = Paragraph(
            fecha_val,
            ParagraphStyle("right", parent=styles["Normal"], alignment=2)
        )

        header = Table([[empresa, fecha]], colWidths=[300, 200])
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP")
        ]))
        story.append(header)
        story.append(Spacer(1, 20))

        # ----------------- TABLA DETALLE -----------------
        data = [
            [
                Paragraph("<b>Producto</b>", styles["Normal"]),
                Paragraph("<b>Cantidad</b>", styles["Normal"]),
                Paragraph("<b>Precio Unitario</b>", styles["Normal"]),
                Paragraph("<b>Subtotal</b>", styles["Normal"])
            ]
        ]

        subtotal_general = 0

        for nombre, cant, precio, sub in self.items:
            subtotal_general += sub

            data.append([
                Paragraph(nombre, styles["Normal"]),
                Paragraph(str(cant), styles["Normal"]),
                Paragraph(f"${precio:,.0f}".replace(",", "."), styles["Normal"]),
                Paragraph(f"${sub:,.0f}".replace(",", "."), styles["Normal"])
            ])

        tabla = Table(
            data,
            colWidths=[250, 80, 120, 120]
        )
        tabla.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFEFEF")),
            ("ALIGN", (1, 1), (-1, -1), "CENTER")
        ]))

        story.append(tabla)
        story.append(Spacer(1, 15))

        # ----------------- TOTALES -----------------
        iva = subtotal_general * 0.19
        total_final = subtotal_general + iva

        totales = Table([
            ["", "Subtotal:", f"${subtotal_general:,.0f}".replace(",", ".")],
            ["", "IVA (19%):", f"${iva:,.0f}".replace(",", ".")],
            ["", Paragraph("<b>Total:</b>", styles["Normal"]),
             f"${total_final:,.0f}".replace(",", ".")]
        ], colWidths=[250, 150, 120])

        totales.setStyle(TableStyle([
            ("ALIGN", (2, 0), (2, -1), "RIGHT")
        ]))

        story.append(totales)
        story.append(Spacer(1, 20))

        story.append(Paragraph(
            "Gracias por su compra.",
            styles["Normal"]
        ))

        # ----------------- GENERAR PDF -----------------
        doc.build(story)
        return salida
