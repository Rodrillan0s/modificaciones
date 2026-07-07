def generar_html_comprobante(nombre_paciente, id_cita, fecha_pago, metodo_pago, monto_bob, monto_usd, saldo_restante_bob, items):
    items_rows = ""
    for i, item in enumerate(items):
        items_rows += f"""
        <tr style="border-bottom: 1px solid #E4EFEF;">
          <td style="padding: 10px; font-size: 12px; color: #333;">{i+1}</td>
          <td style="padding: 10px; font-size: 12px; color: #333;"><strong>{item['nombre']}</strong></td>
          <td style="padding: 10px; font-size: 12px; color: #333; text-align: right; font-weight: bold;">{item['precio']:.2f} BOB</td>
        </tr>
        """

    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 20px; background-color: #F4F9F9;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #E4EFEF;">
          <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #2A5C4D; margin: 0; font-style: italic; font-weight: 900;">CLÍNICA ODONTOLÓGICA ALBA</h2>
            <p style="color: #148F77; font-size: 10px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; margin-top: 5px;">Comprobante de Pago Recibido</p>
          </div>
          
          <div style="border-bottom: 2px dashed #E4EFEF; padding-bottom: 20px; margin-bottom: 20px;">
            <p style="margin: 5px 0; font-size: 13px; color: #666;"><strong>Paciente:</strong> {nombre_paciente}</p>
            <p style="margin: 5px 0; font-size: 13px; color: #666;"><strong>Cita ID:</strong> #{id_cita}</p>
            <p style="margin: 5px 0; font-size: 13px; color: #666;"><strong>Fecha de Pago:</strong> {fecha_pago}</p>
            <p style="margin: 5px 0; font-size: 13px; color: #666;"><strong>Método de Pago:</strong> {metodo_pago}</p>
          </div>
          
          <div style="margin-bottom: 30px;">
            <h3 style="color: #2A5C4D; font-size: 14px; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px;">Detalle de la Cita</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
              <thead>
                <tr style="background-color: #2A5C4D; color: #ffffff;">
                  <th style="padding: 10px; font-size: 11px; text-align: left;">N°</th>
                  <th style="padding: 10px; font-size: 11px; text-align: left;">Concepto / Servicio</th>
                  <th style="padding: 10px; font-size: 11px; text-align: right;">Total</th>
                </tr>
              </thead>
              <tbody>
                {items_rows}
              </tbody>
            </table>

            <h3 style="color: #2A5C4D; font-size: 14px; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;">Resumen de la Transacción</h3>
            <table style="width: 100%; border-collapse: collapse;">
              <tr style="border-bottom: 1px solid #F0F7F7;">
                <td style="padding: 10px 0; font-size: 13px; color: #666;">Monto Cancelado (BOB)</td>
                <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #2A5C4D;">{monto_bob:.2f} BOB</td>
              </tr>
              <tr style="border-bottom: 1px solid #F0F7F7;">
                <td style="padding: 10px 0; font-size: 13px; color: #666;">Equivalente en Dólares (USD)</td>
                <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #2A5C4D;">${monto_usd:.2f} USD</td>
              </tr>
              <tr>
                <td style="padding: 15px 0 10px 0; font-size: 14px; font-weight: bold; color: #333;">Saldo Pendiente Actual</td>
                <td style="padding: 15px 0 10px 0; text-align: right; font-weight: bold; font-size: 16px; color: #D32F2F;">{saldo_restante_bob:.2f} BOB</td>
              </tr>
            </table>
          </div>
          
          <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #E4EFEF;">
            <p style="font-size: 11px; color: #999; margin: 0;">Gracias por confiar su salud dental a nosotros.</p>
            <p style="font-size: 10px; color: #aaa; margin: 5px 0 0 0;">Este correo contiene el comprobante formal de pago adjunto en formato PDF.</p>
            <p style="font-size: 10px; color: #aaa; margin: 5px 0 0 0;">Este es un comprobante automatizado emitido por el sistema de Clínica Alba.</p>
          </div>
        </div>
      </body>
    </html>
    """

def generar_html_recordatorio_citas(odontologo_nombre, citas):
    rows = ""
    for idx, cita in enumerate(citas):
        rows += f"""
        <tr style="border-bottom: 1px solid #E4EFEF;">
            <td style="padding: 10px; font-size: 12px; color: #333;">{idx+1}</td>
            <td style="padding: 10px; font-size: 12px; color: #333;"><strong>{cita['paciente']}</strong></td>
            <td style="padding: 10px; font-size: 12px; color: #333;">{cita['fecha_agendamiento']}</td>
            <td style="padding: 10px; font-size: 12px; color: #333;">{cita['sala']}</td>
            <td style="padding: 10px; font-size: 12px; color: #333;">{cita['procedimiento']}</td>
        </tr>
        """
    if not rows:
        rows = """
        <tr>
            <td colspan="5" style="padding: 20px; font-size: 13px; color: #666; text-align: center; font-style: italic;">
                No tiene citas agendadas para el día de hoy.
            </td>
        </tr>
        """
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 20px; background-color: #F4F9F9;">
        <div style="max-width: 650px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #E4EFEF;">
          <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #2A5C4D; margin: 0; font-style: italic; font-weight: 900;">CLÍNICA ODONTOLÓGICA ALBA</h2>
            <p style="color: #148F77; font-size: 10px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; margin-top: 5px;">Recordatorio Diario de Citas</p>
          </div>
          
          <div style="margin-bottom: 20px;">
            <p style="font-size: 14px; color: #333;">Estimado(a) Dr(a). <strong>{odontologo_nombre}</strong>,</p>
            <p style="font-size: 13px; color: #666; line-height: 1.5;">A continuación, se detalla la agenda de citas programadas para el día de hoy. Además, se adjunta un reporte detallado en PDF.</p>
          </div>
          
          <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <thead>
              <tr style="background-color: #2A5C4D; color: #ffffff;">
                <th style="padding: 10px; font-size: 11px; text-align: left;">N°</th>
                <th style="padding: 10px; font-size: 11px; text-align: left;">Paciente</th>
                <th style="padding: 10px; font-size: 11px; text-align: left;">Hora</th>
                <th style="padding: 10px; font-size: 11px; text-align: left;">Sala</th>
                <th style="padding: 10px; font-size: 11px; text-align: left;">Tratamiento</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>
          
          <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #E4EFEF;">
            <p style="font-size: 11px; color: #999; margin: 0;">Que tenga una excelente jornada de trabajo.</p>
            <p style="font-size: 10px; color: #aaa; margin: 5px 0 0 0;">Este es un recordatorio automático emitido por el sistema de Clínica Alba.</p>
          </div>
        </div>
      </body>
    </html>
    """

def generar_html_reporte_financiero(fecha, kpis):
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 20px; background-color: #F4F9F9;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #E4EFEF;">
          <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #2A5C4D; margin: 0; font-style: italic; font-weight: 900;">CLÍNICA ODONTOLÓGICA ALBA</h2>
            <p style="color: #148F77; font-size: 10px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; margin-top: 5px;">Reporte Consolidado Financiero</p>
          </div>
          
          <div style="border-bottom: 2px dashed #E4EFEF; padding-bottom: 20px; margin-bottom: 20px;">
            <p style="margin: 5px 0; font-size: 13px; color: #666;"><strong>Fecha del Reporte:</strong> {fecha}</p>
          </div>
          
          <div style="margin-bottom: 30px;">
            <h3 style="color: #2A5C4D; font-size: 14px; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;">Resumen Financiero del Periodo</h3>
            <table style="width: 100%; border-collapse: collapse;">
              <tr style="border-bottom: 1px solid #F0F7F7;">
                <td style="padding: 10px 0; font-size: 13px; color: #666;">Total Ingresos Liquidados</td>
                <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #2A5C4D; font-size: 15px;">{kpis.get('total_ingresos', 0.0):.2f} BOB</td>
              </tr>
              <tr style="border-bottom: 1px solid #F0F7F7;">
                <td style="padding: 10px 0; font-size: 13px; color: #666;">Total Cobrado (Amortizado)</td>
                <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #148F77;">{kpis.get('total_amortizado', 0.0):.2f} BOB</td>
              </tr>
              <tr style="border-bottom: 1px solid #F0F7F7;">
                <td style="padding: 10px 0; font-size: 13px; color: #666;">Total de Cuentas por Cobrar (Saldos)</td>
                <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #D32F2F;">{kpis.get('saldo_pendiente', 0.0):.2f} BOB</td>
              </tr>
              <tr>
                <td style="padding: 15px 0 10px 0; font-size: 13px; color: #666;">Cantidad de Transacciones Realizadas</td>
                <td style="padding: 15px 0 10px 0; text-align: right; font-weight: bold; font-size: 15px; color: #333;">{kpis.get('total_transacciones', 0)} transacciones</td>
              </tr>
            </table>
          </div>
          
          <div style="background-color: #F4F9F9; padding: 15px; border-radius: 10px; border-left: 4px solid #148F77; font-size: 12px; color: #555; line-height: 1.4; margin-bottom: 20px;">
            <strong>Nota:</strong> Se adjunta a este correo un reporte detallado en formato PDF del balance general del periodo.
          </div>
          
          <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #E4EFEF;">
            <p style="font-size: 11px; color: #999; margin: 0;">Clínica Odontológica Alba • Reporte Financiero Automatizado</p>
          </div>
        </div>
      </body>
    </html>
    """

def generar_html_reporte_inventario(fecha, kpis):
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 20px; background-color: #F4F9F9;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #E4EFEF;">
          <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="color: #2A5C4D; margin: 0; font-style: italic; font-weight: 900;">CLÍNICA ODONTOLÓGICA ALBA</h2>
            <p style="color: #148F77; font-size: 10px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; margin-top: 5px;">Reporte Consolidado de Inventario</p>
          </div>
          
          <div style="border-bottom: 2px dashed #E4EFEF; padding-bottom: 20px; margin-bottom: 20px;">
            <p style="margin: 5px 0; font-size: 13px; color: #666;"><strong>Fecha del Reporte:</strong> {fecha}</p>
          </div>
          
          <div style="margin-bottom: 30px;">
            <h3 style="color: #2A5C4D; font-size: 14px; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;">Valorización del Almacén</h3>
            <table style="width: 100%; border-collapse: collapse;">
              <tr style="border-bottom: 1px solid #F0F7F7;">
                <td style="padding: 10px 0; font-size: 13px; color: #666;">Valor Total (Costo Compra)</td>
                <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #2A5C4D; font-size: 15px;">{kpis.get('total_compra', 0.0):.2f} BOB</td>
              </tr>
              <tr style="border-bottom: 1px solid #F0F7F7;">
                <td style="padding: 10px 0; font-size: 13px; color: #666;">Valor Comercial Estimado (Venta)</td>
                <td style="padding: 10px 0; text-align: right; font-weight: bold; color: #148F77;">{kpis.get('total_venta', 0.0):.2f} BOB</td>
              </tr>
              <tr>
                <td style="padding: 15px 0 10px 0; font-size: 13px; color: #666;">Ganancia / Margen Proyectado</td>
                <td style="padding: 15px 0 10px 0; text-align: right; font-weight: bold; font-size: 15px; color: #2E7D32;">{kpis.get('utilidad', 0.0):.2f} BOB</td>
              </tr>
            </table>
          </div>
          
          <div style="background-color: #F4F9F9; padding: 15px; border-radius: 10px; border-left: 4px solid #148F77; font-size: 12px; color: #555; line-height: 1.4; margin-bottom: 20px;">
            <strong>Nota:</strong> Se adjunta a este correo el reporte detallado del inventario en formato PDF del almacén general.
          </div>
          
          <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #E4EFEF;">
            <p style="font-size: 11px; color: #999; margin: 0;">Clínica Odontológica Alba • Reporte de Inventario Automatizado</p>
          </div>
        </div>
      </body>
    </html>
    """
