# carta.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generar_menu_pdf(menus, salida="carta.pdf"):
    """
    Genera un PDF con la carta del restaurante.
    Recibe: menus = [(nombre, precio), ...]
    """
    doc = SimpleDocTemplate(
        salida, pagesize=letter,
        leftMargin=36, rightMargin=36,
        topMargin=36, bottomMargin=36
    )

    styles = getSampleStyleSheet()
    story = []

    # ----------------- ENCABEZADO -----------------
    header = Paragraph(
        "<b>Restaurante Crunch — Carta</b><br/>Primavera 2025",
        ParagraphStyle("hdr", parent=styles["Heading1"], textColor=colors.white)
    )

    header_table = Table([[header]], colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2B9BE6")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    story.append(header_table)
    story.append(Spacer(1, 20))

    # ----------------- TABLA DE MENÚS -----------------
    data = [
        [
            Paragraph("<b>Menú</b>", styles["Normal"]),
            Paragraph("<b>Precio</b>", styles["Normal"])
        ]
    ]

    for nombre, precio in menus:
        data.append([
            Paragraph(nombre, styles["Normal"]),
            Paragraph(f"${precio:,.0f}".replace(",", "."), styles["Normal"])
        ])

    tabla = Table(data, colWidths=[350, 100])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F5F7FA")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.gray),
        ("BOX", (0, 0), (-1, -1), 0.3, colors.gray),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    story.append(tabla)
    story.append(Spacer(1, 20))

    # ----------------- GENERAR PDF -----------------
    doc.build(story)
    return salida
