import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from ..config import Config

def generate_receipt_pdf(nombre_paciente, id_cita, fecha_pago, metodo_pago, monto_bob, monto_usd, saldo_restante_bob, items):
    """
    Generates a professional receipt PDF in memory and returns it as a base64 encoded string.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#2A5C4D'),
        alignment=1, # Center
        spaceAfter=5
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#148F77'),
        alignment=1, # Center
        spaceAfter=25
    )
    header_section_style = ParagraphStyle(
        'HeaderSecStyle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#2A5C4D'),
        spaceBefore=15,
        spaceAfter=10
    )
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=9,
        leading=12
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12
    )
    
    # Header Title
    story.append(Paragraph("CLÍNICA ODONTOLÓGICA ALBA", title_style))
    story.append(Paragraph("COMPROBANTE OFICIAL DE PAGO", subtitle_style))
    
    # Info Block Table
    info_data = [
        [Paragraph("<b>Paciente:</b>", cell_bold), Paragraph(nombre_paciente, cell_style),
         Paragraph("<b>Factura/Recibo:</b>", cell_bold), Paragraph(f"REC-{id_cita}", cell_style)],
        [Paragraph("<b>Cita ID:</b>", cell_bold), Paragraph(f"#{id_cita}", cell_style),
         Paragraph("<b>Fecha Emisión:</b>", cell_bold), Paragraph(fecha_pago, cell_style)],
        [Paragraph("<b>Método de Pago:</b>", cell_bold), Paragraph(metodo_pago, cell_style),
         Paragraph("<b>Estado Cuenta:</b>", cell_bold), Paragraph("REGISTRADO", cell_style)]
    ]
    info_table = Table(info_data, colWidths=[100, 160, 110, 130])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4F9F9')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E4EFEF')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E4EFEF')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))
    
    # Details Section
    story.append(Paragraph("Detalle de Servicios / Procedimientos", header_section_style))
    
    # Details Table Header style helper
    header_cell_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white,
        leading=12
    )

    # Details Table
    details_data = [
        [
            Paragraph("N°", header_cell_style),
            Paragraph("Concepto / Descripción", header_cell_style),
            Paragraph("Total (BOB)", header_cell_style)
        ]
    ]
    for idx, item in enumerate(items):
        details_data.append([
            Paragraph(str(idx + 1), cell_style),
            Paragraph(f"<b>{item['nombre']}</b><br/><font color='#777'>Tratamiento dental integrado</font>", cell_style),
            Paragraph(f"{item['precio']:.2f} BOB", cell_style)
        ])
    
    details_table = Table(details_data, colWidths=[30, 360, 110])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2A5C4D')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E4EFEF')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E4EFEF')),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 15))
    
    # Totals Table
    totals_data = [
        [Paragraph("", cell_style), Paragraph("<b>Total Cancelado (BOB):</b>", cell_bold), Paragraph(f"<b>{monto_bob:.2f} BOB</b>", cell_bold)],
        [Paragraph("", cell_style), Paragraph("<b>Equivalente (USD):</b>", cell_bold), Paragraph(f"${monto_usd:.2f} USD", cell_style)],
        [Paragraph("", cell_style), Paragraph("<b>Saldo Pendiente Restante:</b>", cell_bold), Paragraph(f"{saldo_restante_bob:.2f} BOB", cell_style)]
    ]
    totals_table = Table(totals_data, colWidths=[280, 140, 80])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 40))
    
    # Footer Section
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.gray,
        alignment=1
    )
    story.append(Paragraph("Clínica Odontológica Alba • Sonrisas que Inspiran", footer_style))
    story.append(Paragraph("Av. San Martín #145, Edif. Sonrisas • Teléfonos: 3-3456789 • Santa Cruz, Bolivia", footer_style))
    
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Return base64 encoded string
    return base64.b64encode(pdf_bytes).decode('utf-8')
