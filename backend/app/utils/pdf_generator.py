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

def generate_appointments_pdf(citas, title="AGENDA DIARIA DE CITAS"):
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
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyleApp',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#2A5C4D'),
        alignment=1,
        spaceAfter=15
    )
    cell_style = ParagraphStyle(
        'CellApp',
        parent=styles['Normal'],
        fontSize=9,
        leading=12
    )
    cell_bold = ParagraphStyle(
        'CellBoldApp',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12
    )
    header_cell_style = ParagraphStyle(
        'HeaderCellApp',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white,
        leading=12
    )
    
    story.append(Paragraph("CLÍNICA ODONTOLÓGICA ALBA", title_style))
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10))
    
    table_data = [
        [
            Paragraph("N°", header_cell_style),
            Paragraph("Paciente", header_cell_style),
            Paragraph("Fecha / Hora", header_cell_style),
            Paragraph("Sala", header_cell_style),
            Paragraph("Procedimiento / Nota", header_cell_style)
        ]
    ]
    for idx, c in enumerate(citas):
        table_data.append([
            Paragraph(str(idx + 1), cell_style),
            Paragraph(str(c.get('paciente', 'N/A')), cell_bold),
            Paragraph(str(c.get('fecha_agendamiento', 'N/A')), cell_style),
            Paragraph(str(c.get('sala', 'N/A')), cell_style),
            Paragraph(str(c.get('procedimiento', 'N/A')), cell_style)
        ])
    
    if len(citas) == 0:
        table_data.append([
            Paragraph("", cell_style),
            Paragraph("No hay citas registradas para este periodo.", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style)
        ])
        
    table = Table(table_data, colWidths=[30, 130, 110, 80, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2A5C4D')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E4EFEF')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E4EFEF')),
    ]))
    story.append(table)
    
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'FooterStyleApp',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.gray,
        alignment=1
    )
    story.append(Paragraph("Clínica Odontológica Alba • Reporte Automático de Citas", footer_style))
    
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return base64.b64encode(pdf_bytes).decode('utf-8')

def generate_finances_pdf(kpis, title="REPORTE CONSOLIDADO FINANCIERO"):
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
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyleFin',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#2A5C4D'),
        alignment=1,
        spaceAfter=15
    )
    cell_style = ParagraphStyle(
        'CellFin',
        parent=styles['Normal'],
        fontSize=10,
        leading=14
    )
    cell_bold = ParagraphStyle(
        'CellBoldFin',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14
    )
    
    story.append(Paragraph("CLÍNICA ODONTOLÓGICA ALBA", title_style))
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))
    
    table_data = [
        [Paragraph("<b>Métrica / Indicador</b>", cell_bold), Paragraph("<b>Valor en Bolivianos (BOB)</b>", cell_bold)],
        [Paragraph("Total Ingresos Liquidados", cell_style), Paragraph(f"{kpis.get('total_ingresos', 0.0):.2f} BOB", cell_bold)],
        [Paragraph("Monto Amortizado (Cobrado)", cell_style), Paragraph(f"{kpis.get('total_amortizado', 0.0):.2f} BOB", cell_style)],
        [Paragraph("Cuentas por Cobrar (Saldo Pendiente)", cell_style), Paragraph(f"{kpis.get('saldo_pendiente', 0.0):.2f} BOB", cell_style)],
        [Paragraph("Cantidad de Transacciones", cell_style), Paragraph(f"{kpis.get('total_transacciones', 0)} cobros", cell_style)]
    ]
    
    table = Table(table_data, colWidths=[250, 250])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F4F9F9')),
        ('PADDING', (0,0), (-1,-1), 12),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E4EFEF')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E4EFEF')),
    ]))
    story.append(table)
    
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'FooterStyleFin',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.gray,
        alignment=1
    )
    story.append(Paragraph("Clínica Odontológica Alba • Reporte Financiero Automatizado", footer_style))
    
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return base64.b64encode(pdf_bytes).decode('utf-8')

def generate_inventario_pdf(data, title="REPORTE DE INVENTARIO Y VALORIZACIÓN"):
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
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyleInv',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#2A5C4D'),
        alignment=1,
        spaceAfter=15
    )
    cell_style = ParagraphStyle(
        'CellInv',
        parent=styles['Normal'],
        fontSize=9,
        leading=12
    )
    cell_bold = ParagraphStyle(
        'CellBoldInv',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12
    )
    header_cell_style = ParagraphStyle(
        'HeaderCellInv',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white,
        leading=12
    )
    
    story.append(Paragraph("CLÍNICA ODONTOLÓGICA ALBA", title_style))
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))
    
    # Summary Table first
    summary_data = [
        [Paragraph("<b>Valor Almacén (Compra)</b>", cell_bold), Paragraph(f"{data.get('kpis', {}).get('total_compra', 0.0):.2f} BOB", cell_bold)],
        [Paragraph("<b>Valor Comercial (Venta)</b>", cell_bold), Paragraph(f"{data.get('kpis', {}).get('total_venta', 0.0):.2f} BOB", cell_bold)],
        [Paragraph("<b>Margen Proyectado</b>", cell_bold), Paragraph(f"{data.get('kpis', {}).get('utilidad', 0.0):.2f} BOB", cell_bold)]
    ]
    summary_table = Table(summary_data, colWidths=[250, 250])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4F9F9')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E4EFEF')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E4EFEF')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    # Items Table Header
    table_data = [
        [
            Paragraph("ID", header_cell_style),
            Paragraph("Descripción Material", header_cell_style),
            Paragraph("Costo Compra", header_cell_style),
            Paragraph("Precio Venta", header_cell_style),
            Paragraph("Existencia", header_cell_style),
            Paragraph("Total Costo", header_cell_style)
        ]
    ]
    
    for idx, item in enumerate(data.get('items', [])[:25]):  # Limit to top 25 items for visual space
        table_data.append([
            Paragraph(str(item.get('id', 'N/A')), cell_style),
            Paragraph(str(item.get('descripcion', 'N/A')), cell_bold),
            Paragraph(f"{item.get('precio', 0.0):.2f} BOB", cell_style),
            Paragraph(f"{item.get('precio_venta', 0.0):.2f} BOB", cell_style),
            Paragraph(f"{item.get('metrica_core', 0)} u.", cell_style),
            Paragraph(f"{item.get('costo_total', 0.0):.2f} BOB", cell_bold)
        ])
        
    if len(data.get('items', [])) == 0:
        table_data.append([
            Paragraph("", cell_style),
            Paragraph("No hay insumos registrados en el almacén.", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style)
        ])
        
    table = Table(table_data, colWidths=[40, 160, 75, 75, 65, 85])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2A5C4D')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E4EFEF')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E4EFEF')),
    ]))
    story.append(table)
    
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'FooterStyleInv',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.gray,
        alignment=1
    )
    story.append(Paragraph("Clínica Odontológica Alba • Reporte de Inventario Automatizado", footer_style))
    
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return base64.b64encode(pdf_bytes).decode('utf-8')

def generate_patients_pdf(data_list, title):
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
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStylePat',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#2A5C4D'),
        alignment=1,
        spaceAfter=15
    )
    cell_style = ParagraphStyle('CellPat', parent=styles['Normal'], fontSize=8, leading=10)
    cell_bold = ParagraphStyle('CellPatB', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', leading=10)
    header_cell_style = ParagraphStyle('HCellPat', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=colors.white, leading=10)
    
    story.append(Paragraph("CLÍNICA ODONTOLÓGICA ALBA", title_style))
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))
    
    table_data = [
        [
            Paragraph("ID", header_cell_style),
            Paragraph("Nombre", header_cell_style),
            Paragraph("CI", header_cell_style),
            Paragraph("Teléfono", header_cell_style),
            Paragraph("Citas", header_cell_style),
            Paragraph("Comple.", header_cell_style),
            Paragraph("Total Pagado", header_cell_style),
            Paragraph("Pendiente", header_cell_style)
        ]
    ]
    
    for item in data_list[:30]:
        table_data.append([
            Paragraph(str(item.get('id_paciente', 'N/A')), cell_style),
            Paragraph(str(item.get('nombre', 'N/A')), cell_bold),
            Paragraph(str(item.get('ci', 'N/A')), cell_style),
            Paragraph(str(item.get('telefono', 'N/A')), cell_style),
            Paragraph(str(item.get('total_citas', 0)), cell_style),
            Paragraph(str(item.get('completadas', 0)), cell_style),
            Paragraph(f"{item.get('total_pagado', 0.0):.2f} BOB", cell_style),
            Paragraph(f"{item.get('saldo_pendiente', 0.0):.2f} BOB", cell_style)
        ])
        
    if len(data_list) == 0:
        table_data.append([Paragraph("", cell_style)] * 8)
        table_data[-1][1] = Paragraph("No hay pacientes registrados en el periodo.", cell_style)
        
    table = Table(table_data, colWidths=[35, 125, 60, 65, 40, 45, 75, 75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2A5C4D')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E4EFEF')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E4EFEF')),
    ]))
    story.append(table)
    
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle('FooterPat', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.gray, alignment=1)
    story.append(Paragraph("Clínica Odontológica Alba • Reporte de Pacientes", footer_style))
    
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return base64.b64encode(pdf_bytes).decode('utf-8')

def generate_administration_pdf(data_list, title, tipo):
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
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyleAdmin',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#2A5C4D'),
        alignment=1,
        spaceAfter=15
    )
    cell_style = ParagraphStyle('CellAdm', parent=styles['Normal'], fontSize=8, leading=10)
    cell_bold = ParagraphStyle('CellAdmB', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', leading=10)
    header_cell_style = ParagraphStyle('HCellAdm', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', textColor=colors.white, leading=10)
    
    story.append(Paragraph("CLÍNICA ODONTOLÓGICA ALBA", title_style))
    story.append(Paragraph(f"{title} ({tipo.upper()})", title_style))
    story.append(Spacer(1, 20))
    
    col_widths = [50, 220, 130, 120]
    if tipo == 'salas':
        table_data = [
            [
                Paragraph("ID", header_cell_style),
                Paragraph("Nombre Sala", header_cell_style),
                Paragraph("Tipo Sala", header_cell_style),
                Paragraph("Estado", header_cell_style),
                Paragraph("Total Citas", header_cell_style),
                Paragraph("Completadas", header_cell_style),
                Paragraph("Canceladas", header_cell_style)
            ]
        ]
        col_widths = [40, 120, 90, 80, 60, 70, 60]
        for item in data_list[:30]:
            table_data.append([
                Paragraph(str(item.get('id_sala', 'N/A')), cell_style),
                Paragraph(str(item.get('nombre_sala', 'N/A')), cell_bold),
                Paragraph(str(item.get('tipo_sala', 'N/A')), cell_style),
                Paragraph(str(item.get('estado_sala', 'N/A')), cell_style),
                Paragraph(str(item.get('total_citas', 0)), cell_style),
                Paragraph(str(item.get('completadas', 0)), cell_style),
                Paragraph(str(item.get('canceladas', 0)), cell_style)
            ])
    elif tipo == 'servicios':
        table_data = [
            [
                Paragraph("ID", header_cell_style),
                Paragraph("Servicio", header_cell_style),
                Paragraph("Precio Sugerido", header_cell_style),
                Paragraph("Solicitudes", header_cell_style),
                Paragraph("Ingresos Estimados", header_cell_style)
            ]
        ]
        col_widths = [50, 200, 100, 80, 90]
        for item in data_list[:30]:
            table_data.append([
                Paragraph(str(item.get('id_servicio', 'N/A')), cell_style),
                Paragraph(str(item.get('nombre_servicio', 'N/A')), cell_bold),
                Paragraph(f"{item.get('precio_sugerido', 0.0):.2f} BOB", cell_style),
                Paragraph(str(item.get('total_solicitudes', 0)), cell_style),
                Paragraph(f"{item.get('ingresos_estimados', 0.0):.2f} BOB", cell_bold)
            ])
    else:
        table_data = [
            [
                Paragraph("ID", header_cell_style),
                Paragraph("Descripción / Nombre", header_cell_style),
                Paragraph("Métrica / Detalle", header_cell_style),
                Paragraph("Ingresos / Citas", header_cell_style)
            ]
        ]
        col_widths = [50, 220, 130, 120]
        for item in data_list[:30]:
            desc = item.get('descripcion') or item.get('nombre_completo') or 'N/A'
            detail = item.get('servicio_nombre') or item.get('especialidad') or 'N/A'
            metric = item.get('ingresos_estimados') or item.get('citas_atendidas') or 0
            metric_str = f"{metric:.2f} BOB" if isinstance(metric, float) else str(metric)
            table_data.append([
                Paragraph(str(item.get('id_procedimiento') or item.get('id_personal') or 'N/A'), cell_style),
                Paragraph(str(desc), cell_bold),
                Paragraph(str(detail), cell_style),
                Paragraph(metric_str, cell_bold)
            ])
            
    if len(data_list) == 0:
        table_data.append([Paragraph("No hay registros en el periodo.", cell_style)] * len(table_data[0]))
        
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2A5C4D')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E4EFEF')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E4EFEF')),
    ]))
    story.append(table)
    
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle('FooterAdm', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.gray, alignment=1)
    story.append(Paragraph("Clínica Odontológica Alba • Reporte Administrativo", footer_style))
    
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return base64.b64encode(pdf_bytes).decode('utf-8')
