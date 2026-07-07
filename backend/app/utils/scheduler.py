import threading
import time
import traceback
from datetime import datetime, date
from ..config import db, Config
from .email_sender import send_email_brevo
from .email_templates import generar_html_recordatorio_citas, generar_html_reporte_financiero, generar_html_reporte_inventario
from .pdf_generator import generate_appointments_pdf, generate_finances_pdf, generate_inventario_pdf, generate_patients_pdf, generate_administration_pdf
from ..services.bitacora import Bitacora

def obtener_descripcion_reporte(modulo, subtab):
    mod = modulo.lower().strip()
    sub = (subtab or '').lower().strip()
    
    if mod == 'citas':
        if sub == 'global_odontologos':
            return "Consolidado Global de Odontólogos"
        elif sub == 'pacientes':
            return "Historial de Citas por Paciente"
        elif sub == 'odontologos':
            return "Historial de Citas por Odontólogo"
        else:
            return "Consolidado Global de Pacientes"
            
    elif mod == 'finanzas':
        if sub == 'mensual':
            return "Evolución Mensual Financiera"
        elif sub == 'odontologos':
            return "Ingresos por Odontólogo"
        elif sub == 'procedimientos':
            return "Ingresos por Procedimiento"
        elif sub == 'metodos':
            return "Métodos de Pago"
        elif sub == 'saldos':
            return "Saldos y Amortizaciones"
        else:
            return "Resumen General Financiero"
            
    elif mod == 'inventario':
        if sub == 'mermas':
            return "Mermas / Pérdidas de Inventario"
        elif sub == 'ingresos':
            return "Entradas y Abastecimiento de Inventario"
        elif sub == 'vencimientos':
            return "Lotes Próximos a Vencer"
        elif sub == 'estatico':
            return "Corte de Stock Estático"
        else:
            return "Existencias de Insumos (Inventario General)"
            
    elif mod == 'pacientes':
        if sub == 'general':
            return "Frecuencia y Visitas Totales de Pacientes"
        elif sub == 'frecuentes':
            return "Pacientes Más Frecuentes"
        elif sub == 'aportes':
            return "Pacientes de Mayor Aporte"
        elif sub == 'deudores':
            return "Saldos Deudores Activos de Pacientes"
        elif sub == 'inactivos':
            return "Pacientes Inactivos"
        else:
            return "Resumen General de Pacientes"
            
    elif mod == 'administracion':
        if sub == 'servicios':
            return "Solicitudes de Servicios"
        elif sub == 'procedimientos':
            return "Rendimiento de Procedimientos"
        elif sub == 'personal':
            return "Apoyo de Personal Médico"
        else:
            return "Ocupación de Consultorios (Salas)"
            
    return "Reporte General"

def recordatorio_Citas(para_list=None, is_manual=False, f_inicio='', f_fin='', tipo='global'):
    """
    CU35 - Enviar Recordatorio Diario de Citas.
    Obtiene las citas y las envía al odontólogo o administradores con filtros opcionales.
    """
    try:
        if not para_list:
            para_list = []
            
        query = f"""
            SELECT 
                c.id_cita,
                c.fecha_agendamiento,
                p.nombre AS paciente,
                o.nombre AS odontologo,
                o_u.correo AS odontologo_correo,
                s.nombre AS sala,
                pr.descripcion AS procedimiento
            FROM {Config.SCHEMA}.t_citas c
            JOIN {Config.SCHEMA}.t_persona p ON c.id_paciente = p.id_persona
            JOIN {Config.SCHEMA}.t_personal pers ON c.id_personal = pers.id_personal
            JOIN {Config.SCHEMA}.t_persona o ON pers.id_personal = o.id_persona
            JOIN {Config.SCHEMA}.t_usuario o_u ON o.id_persona = o_u.id_persona
            JOIN {Config.SCHEMA}.t_sala s ON c.id_sala = s.id_sala
            JOIN {Config.SCHEMA}.t_procedimiento pr ON c.id_procedimiento = pr.id_procedimiento
            WHERE 1=1
        """
        params = []
        if f_inicio:
            query += " AND DATE(c.fecha_agendamiento) >= %s"
            params.append(f_inicio)
        if f_fin:
            query += " AND DATE(c.fecha_agendamiento) <= %s"
            params.append(f_fin)
        if not f_inicio and not f_fin:
            query += " AND DATE(c.fecha_agendamiento) = CURRENT_DATE"
            
        query += " ORDER BY c.fecha_agendamiento ASC"
        rows = db.execute_query(query, params, fetchall=True) or []
        
        citas_list = [{
            "id_cita": r[0],
            "fecha_agendamiento": r[1].strftime('%H:%M') if r[1] else "",
            "paciente": r[2],
            "odontologo": r[3],
            "odontologo_correo": r[4],
            "sala": r[5],
            "procedimiento": r[6]
        } for r in rows]

        if is_manual:
            desc = obtener_descripcion_reporte('citas', tipo)
            fecha_str = f"{f_inicio} a {f_fin}" if (f_inicio or f_fin) else date.today().strftime('%d/%m/%Y')
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #2A5C4D;">Reporte de Citas - Clínica Alba</h2>
                <p>Se adjunta el reporte detallado solicitado manualmente: <strong>{desc}</strong>.</p>
                <p><strong>Periodo / Fecha:</strong> {fecha_str}</p>
                <p>Saludos cordiales,<br>Administración Clínica Alba</p>
            </body>
            </html>
            """
            pdf_b64 = generate_appointments_pdf(citas_list, f"REPORTE: {desc.upper()} ({fecha_str})")
            attachments = [{
                "content": pdf_b64,
                "name": f"Reporte_Citas_{tipo}_{fecha_str.replace('/', '-').replace(' ', '_')}.pdf"
            }]
            success = True
            for email in para_list:
                sent = send_email_brevo(email.strip(), f"Reporte de Citas ({desc}) - Clínica Alba", html, attachments=attachments)
                if not sent:
                    success = False
            if success:
                Bitacora.registrar("REPORTES", "EnvioManualDeCorreoCitas", f"Enviado exitosamente a: {', '.join(para_list)} ({desc})")
                return True
            else:
                Bitacora.registrar("REPORTES", "EnvioManualDeCorreoCitasFallido", f"Fallo al enviar a algunos destinatarios: {', '.join(para_list)}")
                return False
        else:
            # Agrupación por correo de odontólogo
            from collections import defaultdict
            grouped = defaultdict(list)
            for c in citas_list:
                grouped[c['odontologo_correo']].append(c)
            
            for o_email, o_citas in grouped.items():
                o_name = o_citas[0]['odontologo']
                html = generar_html_recordatorio_citas(o_name, o_citas)
                pdf_b64 = generate_appointments_pdf(o_citas, f"AGENDA DIARIA - DR(A). {o_name.upper()}")
                attachments = [{
                    "content": pdf_b64,
                    "name": f"Agenda_{o_name.replace(' ', '_')}.pdf"
                }]
                send_email_brevo(o_email, "Su Agenda de Citas para Hoy - Clínica Alba", html, attachments=attachments)
                
            # Envío a destinatarios configurados en la tarea automática
            if para_list:
                html = generar_html_recordatorio_citas("Administración", citas_list)
                pdf_b64 = generate_appointments_pdf(citas_list, "AGENDA COMPLETA DE CITAS")
                attachments = [{
                    "content": pdf_b64,
                    "name": "Agenda_Completa_Citas.pdf"
                }]
                for email in para_list:
                    send_email_brevo(email.strip(), "Resumen Diario de Citas - Clínica Alba", html, attachments=attachments)
            return True
            
    except Exception as e:
        print(f"[SCHEDULER ERROR] Error in recordatorio_Citas: {str(e)}")
        traceback.print_exc()
        if is_manual:
            Bitacora.registrar("REPORTES", "EnvioManualDeCorreoCitasFallido", f"Excepción: {str(e)}")
        return False

def query_financial_kpis(f_inicio='', f_fin=''):
    # 1. Ingresos
    q_ingresos = f"""
        SELECT COALESCE(SUM(monto_cancelado), 0.0)::double precision, COUNT(id_factura)::integer
        FROM {Config.SCHEMA}.t_facturas
        WHERE 1=1
    """
    params_ing = []
    if f_inicio:
        q_ingresos += " AND DATE(fecha_factura) >= %s"
        params_ing.append(f_inicio)
    if f_fin:
        q_ingresos += " AND DATE(fecha_factura) <= %s"
        params_ing.append(f_fin)
    if not f_inicio and not f_fin:
        q_ingresos += " AND DATE(fecha_factura) = CURRENT_DATE"
        
    res_ing = db.execute_query(q_ingresos, params_ing, fetchone=True) or (0.0, 0)
    
    # 2. Saldos y cobros
    q_saldos = f"""
        SELECT 
            COALESCE(SUM(saldo_inicial), 0.0)::double precision, 
            COALESCE(SUM(saldo_actual), 0.0)::double precision
        FROM {Config.SCHEMA}.t_saldo
    """
    res_sal = db.execute_query(q_saldos, fetchone=True) or (0.0, 0.0)
    
    kpis = {
        "total_ingresos": res_ing[0],
        "total_amortizado": res_sal[0] - res_sal[1],
        "saldo_pendiente": res_sal[1],
        "total_transacciones": res_ing[1]
    }
    return kpis

def reporte_financiero(para_list=None, is_manual=False, f_inicio='', f_fin='', tipo='resumen'):
    """
    CU36 - Enviar Reporte Financiero.
    Genera el balance financiero general con filtros opcionales y lo envía con un Excel adjunto.
    """
    try:
        if not para_list:
            para_list = []
            
        kpis = query_financial_kpis(f_inicio, f_fin)
        fecha_str = f"{f_inicio} a {f_fin}" if (f_inicio or f_fin) else date.today().strftime('%d/%m/%Y')
        desc = obtener_descripcion_reporte('finanzas', tipo)
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #2A5C4D;">Reporte Financiero - Clínica Alba</h2>
            <p>Se adjunta el reporte detallado: <strong>{desc}</strong>.</p>
            <p><strong>Periodo:</strong> {fecha_str}</p>
            <p>Saludos cordiales,<br>Administración Clínica Alba</p>
        </body>
        </html>
        """
        pdf_b64 = generate_finances_pdf(kpis, f"REPORTE: {desc.upper()} ({fecha_str})")
        
        # Generar CSV/Excel de transacciones del día
        import base64
        q_transacciones = f"""
            SELECT id_factura, fecha_factura, metodo_pago, monto_cancelado
            FROM {Config.SCHEMA}.t_facturas
            WHERE 1=1
        """
        params_trans = []
        if f_inicio:
            q_transacciones += " AND DATE(fecha_factura) >= %s"
            params_trans.append(f_inicio)
        if f_fin:
            q_transacciones += " AND DATE(fecha_factura) <= %s"
            params_trans.append(f_fin)
        if not f_inicio and not f_fin:
            q_transacciones += " AND DATE(fecha_factura) = CURRENT_DATE"
            
        rows_trans = db.execute_query(q_transacciones, params_trans, fetchall=True) or []
        csv_lines = ["ID Factura;Fecha;Metodo de Pago;Monto Cancelado (BOB)"]
        for rt in rows_trans:
            fecha_t = rt[1].strftime('%d/%m/%Y %H:%M') if rt[1] else ""
            csv_lines.append(f"{rt[0]};{fecha_t};{rt[2]};{rt[3]:.2f}")
        csv_content = "\uFEFF" + "\n".join(csv_lines)
        csv_b64 = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        
        attachments = [
            {
                "content": pdf_b64,
                "name": f"Reporte_Financiero_{tipo}_{fecha_str.replace('/', '-').replace(' ', '_')}.pdf"
            },
            {
                "content": csv_b64,
                "name": f"Detalle_Transacciones_{tipo}_{fecha_str.replace('/', '-').replace(' ', '_')}.csv"
            }
        ]
        
        success = True
        for email in para_list:
            sent = send_email_brevo(email.strip(), f"Reporte Financiero ({desc}) - Clínica Alba", html, attachments=attachments)
            if not sent:
                success = False
                
        if is_manual:
            if success:
                Bitacora.registrar("REPORTES", "Envio_Manual_Financiero", f"Enviado exitosamente a: {', '.join(para_list)} ({desc})")
                return True
            else:
                Bitacora.registrar("REPORTES", "Envio_Manual_Financiero_Fallido", f"Fallo al enviar a algunos destinatarios: {', '.join(para_list)}")
                return False
        return True
    except Exception as e:
        print(f"[SCHEDULER ERROR] Error in reporte_financiero: {str(e)}")
        traceback.print_exc()
        if is_manual:
            Bitacora.registrar("REPORTES", "Envio_Manual_Financiero_Fallido", f"Excepción: {str(e)}")
        return False

def query_inventory_data(tipo='general', f_inicio='', f_fin='', id_proveedor='', id_material='', top=None):
    mat_query = f"SELECT UPPER(nombre_material), precio_venta FROM {Config.SCHEMA}.t_materiales"
    mat_rows = db.execute_query(mat_query, fetchall=True) or []
    precio_venta_lookup = {r[0].strip(): float(r[1]) if r[1] is not None else 0.0 for r in mat_rows}
    
    query = f"""
        SELECT 
            id_insumo, nombre_insumo, precio_catalogo, es_expirable, 
            cantidad_unidades, conteo_lotes_o_incidentes, fecha_referencial, 
            origen_extra, costo_valorizado 
        FROM {Config.SCHEMA}.f_kardex_analitico_universal(
            %s, 'TODOS', 'todos', %s, %s, %s, %s, '', '', '', false, %s
        )
    """
    params = (
        str(tipo),
        str(f_inicio or ''),
        str(f_fin or ''),
        str(id_material or ''),
        str(id_proveedor or ''),
        int(top) if top else None
    )
    rows = db.execute_query(query, params, fetchall=True) or []
    
    items = []
    total_compra = 0.0
    total_venta = 0.0
    for r in rows:
        desc = r[1]
        p_compra = float(r[2]) if r[2] is not None else 0.0
        p_venta = precio_venta_lookup.get(desc.upper().strip() if desc else "", 0.0)
        metrica = int(r[4]) if r[4] is not None else 0
        costo_compra = float(r[8]) if r[8] is not None else 0.0
        costo_venta = float(metrica * p_venta)
        
        total_compra += costo_compra
        total_venta += costo_venta
        
        items.append({
            "id": r[0],
            "descripcion": desc,
            "precio": p_compra,
            "precio_venta": p_venta,
            "metrica_core": metrica,
            "costo_total": costo_compra,
            "costo_total_venta": costo_venta
        })
        
    kpis = {
        "total_compra": total_compra,
        "total_venta": total_venta,
        "utilidad": total_venta - total_compra
    }
    return {"kpis": kpis, "items": items}

def reporte_inventario(para_list=None, is_manual=False, tipo='general', f_inicio='', f_fin='', id_proveedor='', id_material='', top=None):
    """
    CU37 - Enviar Reporte de Inventario.
    Genera la valorización y stock actual del almacén con filtros opcionales y lo envía a los destinatarios con un Excel adjunto.
    """
    try:
        if not para_list:
            para_list = []
            
        data = query_inventory_data(tipo=tipo, f_inicio=f_inicio, f_fin=f_fin, id_proveedor=id_proveedor, id_material=id_material, top=top)
        fecha_str = f"{f_inicio} a {f_fin}" if (f_inicio or f_fin) else date.today().strftime('%d/%m/%Y')
        desc = obtener_descripcion_reporte('inventario', tipo)
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #2A5C4D;">Reporte de Inventario - Clínica Alba</h2>
            <p>Se adjunta el reporte detallado: <strong>{desc}</strong>.</p>
            <p><strong>Periodo:</strong> {fecha_str}</p>
            <p>Saludos cordiales,<br>Administración Clínica Alba</p>
        </body>
        </html>
        """
        pdf_b64 = generate_inventario_pdf(data, f"REPORTE: {desc.upper()} ({fecha_str})")
        
        # Generar CSV/Excel de la lista de insumos del almacén
        import base64
        csv_lines = ["ID Insumo;Descripcion;Costo Compra (BOB);Precio Venta (BOB);Stock;Costo Valorizado (BOB)"]
        for item in data.get('items', []):
            csv_lines.append(f"{item['id']};{item['descripcion']};{item.get('precio', 0.0):.2f};{item.get('precio_venta', 0.0):.2f};{item['metrica_core']};{item.get('costo_total', 0.0):.2f}")
        csv_content = "\uFEFF" + "\n".join(csv_lines)
        csv_b64 = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        
        attachments = [
            {
                "content": pdf_b64,
                "name": f"Reporte_Inventario_{tipo}_{fecha_str.replace('/', '-').replace(' ', '_')}.pdf"
            },
            {
                "content": csv_b64,
                "name": f"Detalle_Inventario_{tipo}_{fecha_str.replace('/', '-').replace(' ', '_')}.csv"
            }
        ]
        
        success = True
        for email in para_list:
            sent = send_email_brevo(email.strip(), f"Reporte de Inventario ({desc}) - Clínica Alba", html, attachments=attachments)
            if not sent:
                success = False
                
        if is_manual:
            if success:
                Bitacora.registrar("REPORTES", "Envio_Manual_Inventario", f"Enviado exitosamente a: {', '.join(para_list)} ({desc})")
                return True
            else:
                Bitacora.registrar("REPORTES", "Envio_Manual_InventarioFallido", f"Fallo al enviar a algunos destinatarios: {', '.join(para_list)}")
                return False
        return True
    except Exception as e:
        print(f"[SCHEDULER ERROR] Error in reporte_inventario: {str(e)}")
        traceback.print_exc()
        if is_manual:
            Bitacora.registrar("REPORTES", "Envio_Manual_InventarioFallido", f"Excepción: {str(e)}")
        return False

# ==========================================
# PLANIFICADOR EN SEGUNDO PLANO
# ==========================================

def run_scheduler_loop(app):
    """Bucle infinito asíncrono para verificar tareas automáticas."""
    print("[SCHEDULER] Hilo de planificación iniciado.")
    
    # 1. Asegurar columna ultimo_envio en base de datos
    with app.app_context():
        try:
            db.execute_query(f"ALTER TABLE {Config.SCHEMA}.t_entidades_mail ADD COLUMN IF NOT EXISTS ultimo_envio TIMESTAMP;", commit=True)
            db.execute_query(f"ALTER TABLE {Config.SCHEMA}.t_entidades_mail ALTER COLUMN para TYPE VARCHAR(500);", commit=True)
            print("[SCHEDULER] Tabla t_entidades_mail inicializada y verificada exitosamente.")
        except Exception as e:
            print(f"[SCHEDULER INIT ERROR] No se pudo alterar/verificar t_entidades_mail: {e}")

    # Ejecutar cada hora
    while True:
        try:
            with app.app_context():
                ahora = datetime.now()
                # Consultar tareas habilitadas
                query = f"""
                    SELECT tarea, entidad, categoria, para, ultimo_envio 
                    FROM {Config.SCHEMA}.t_entidades_mail 
                    WHERE habilitado = true
                """
                tasks = db.execute_query(query, fetchall=True) or []
                
                for task in tasks:
                    tarea, entidad, categoria, para, ultimo_envio = task
                    para_emails = [e.strip() for e in para.split(',') if e.strip()]
                    if not para_emails:
                        continue
                        
                    debe_ejecutar = False
                    
                    # Decisión de ejecución según la frecuencia (categoria)
                    if not ultimo_envio:
                        debe_ejecutar = True
                    else:
                        delta = ahora - ultimo_envio
                        if categoria == 'diario' and delta.days >= 1:
                            debe_ejecutar = True
                        elif categoria == 'semanal' and delta.days >= 7:
                            debe_ejecutar = True
                        elif categoria == 'mensual' and delta.days >= 30:
                            debe_ejecutar = True
                            
                    if debe_ejecutar:
                        print(f"[SCHEDULER] Ejecutando tarea automática: {tarea} ({entidad})")
                        exito = False
                        if entidad == 'citas':
                            exito = recordatorio_Citas(para_emails, is_manual=False)
                        elif entidad == 'finanzas':
                            exito = reporte_financiero(para_emails, is_manual=False)
                        elif entidad == 'inventario':
                            exito = reporte_inventario(para_emails, is_manual=False)
                            
                        if exito:
                            # Actualizar timestamp
                            update_query = f"""
                                UPDATE {Config.SCHEMA}.t_entidades_mail 
                                SET ultimo_envio = %s 
                                WHERE tarea = %s
                            """
                            db.execute_query(update_query, (ahora, tarea), commit=True)
                            print(f"[SCHEDULER] Tarea {tarea} completada exitosamente.")
                            
        except Exception as e:
            print(f"[SCHEDULER LOOP ERROR] {str(e)}")
            traceback.print_exc()
            
        # Esperar 1 hora (3600 segundos) para la siguiente comprobación
        time.sleep(3600)

def query_patients_data(f_inicio='', f_fin='', nombre=''):
    try:
        name_param = f"%{nombre}%" if nombre else None
        query = f"""
            SELECT 
                p.id_persona, p.nombre, p.ci, p.telefono,
                COUNT(c.id_cita)::integer AS total_citas,
                SUM(CASE WHEN c.id_estado_cita = 1 THEN 1 ELSE 0 END)::integer AS programadas,
                SUM(CASE WHEN c.id_estado_cita = 2 THEN 1 ELSE 0 END)::integer AS canceladas,
                SUM(CASE WHEN c.id_estado_cita = 3 THEN 1 ELSE 0 END)::integer AS reprogramadas,
                SUM(CASE WHEN c.id_estado_cita = 4 THEN 1 ELSE 0 END)::integer AS completadas,
                SUM(CASE WHEN c.id_estado_cita = 5 THEN 1 ELSE 0 END)::integer AS no_asistio,
                COALESCE(SUM(f.monto_cancelado), 0)::double precision AS total_pagado,
                COALESCE(SUM(s.saldo_actual), 0)::double precision AS saldo_pendiente,
                MAX(c.fecha_agendamiento) AS ultima_cita
            FROM {Config.SCHEMA}.t_persona p
            INNER JOIN {Config.SCHEMA}.t_paciente pac ON pac.id_paciente = p.id_persona
            LEFT JOIN {Config.SCHEMA}.t_citas c ON c.id_paciente = pac.id_paciente
                AND (%s::timestamp IS NULL OR c.fecha_agendamiento >= %s::timestamp)
                AND (%s::timestamp IS NULL OR c.fecha_agendamiento <= %s::timestamp)
            LEFT JOIN {Config.SCHEMA}.t_facturas f ON f.id_cita = c.id_cita
            LEFT JOIN {Config.SCHEMA}.t_saldo s ON s.id_cita = c.id_cita
            WHERE (%s::text IS NULL OR LOWER(p.nombre) LIKE LOWER(%s::text))
            GROUP BY p.id_persona, p.nombre, p.ci, p.telefono
            ORDER BY total_citas DESC
        """
        params = (
            f_inicio or None, f_inicio or None,
            f_fin or None, f_fin or None,
            name_param, name_param
        )
        rows = db.execute_query(query, params, fetchall=True) or []
        
        data_list = []
        for r in rows:
            data_list.append({
                "id_paciente": r[0],
                "nombre": r[1],
                "ci": r[2],
                "telefono": r[3],
                "total_citas": r[4],
                "completadas": r[7],
                "total_pagado": r[10],
                "saldo_pendiente": r[11]
            })
        return data_list
    except Exception as e:
        print(f"Error querying patients data: {str(e)}")
        return []

def reporte_pacientes(para_list=None, is_manual=False, f_inicio='', f_fin='', nombre='', tipo='resumen'):
    try:
        if not para_list:
            para_list = []
        data_list = query_patients_data(f_inicio, f_fin, nombre)
        fecha_str = f"{f_inicio} a {f_fin}" if (f_inicio or f_fin) else date.today().strftime('%d/%m/%Y')
        desc = obtener_descripcion_reporte('pacientes', tipo)
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #2A5C4D;">Reporte de Pacientes - Clínica Alba</h2>
            <p>Se adjunta el reporte detallado: <strong>{desc}</strong>.</p>
            <p><strong>Periodo:</strong> {fecha_str}</p>
            <p>Saludos cordiales,<br>Administración Clínica Alba</p>
        </body>
        </html>
        """
        
        pdf_b64 = generate_patients_pdf(data_list, f"REPORTE: {desc.upper()} ({fecha_str})")
        
        import base64
        csv_lines = ["ID Paciente;Nombre;CI;Telefono;Total Citas;Completadas;Total Pagado (BOB);Saldo Pendiente (BOB)"]
        for item in data_list:
            csv_lines.append(f"{item['id_paciente']};{item['nombre']};{item['ci']};{item['telefono']};{item['total_citas']};{item['completadas']};{item['total_pagado']:.2f};{item['saldo_pendiente']:.2f}")
        csv_content = "\uFEFF" + "\n".join(csv_lines)
        csv_b64 = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        
        attachments = [
            {
                "content": pdf_b64,
                "name": f"Reporte_Pacientes_{tipo}_{fecha_str.replace('/', '-').replace(' ', '_')}.pdf"
            },
            {
                "content": csv_b64,
                "name": f"Detalle_Pacientes_{tipo}_{fecha_str.replace('/', '-').replace(' ', '_')}.csv"
            }
        ]
        
        success = True
        for email in para_list:
            sent = send_email_brevo(email.strip(), f"Reporte de Pacientes ({desc}) - Clínica Alba", html, attachments=attachments)
            if not sent:
                success = False
                
        if is_manual:
            if success:
                Bitacora.registrar("REPORTES", "Envio_Manual_Pacientes", f"Enviado exitosamente a: {', '.join(para_list)} ({desc})")
                return True
            else:
                Bitacora.registrar("REPORTES", "Envio_Manual_Pacientes_Fallido", f"Fallo al enviar a algunos destinatarios: {', '.join(para_list)}")
                return False
        return True
    except Exception as e:
        print(f"[SCHEDULER ERROR] Error in reporte_pacientes: {str(e)}")
        if is_manual:
            Bitacora.registrar("REPORTES", "Envio_Manual_Pacientes_Fallido", f"Excepción: {str(e)}")
        return False

def query_administration_data(tipo='salas', f_inicio='', f_fin=''):
    try:
        f_desde = f_inicio or None
        f_hasta = f_fin or None
        if tipo == 'salas':
            query = f"""
                SELECT 
                    s.id_sala, s.nombre AS nombre_sala, s.tipo_sala, s.estado_sala,
                    COUNT(c.id_cita)::integer AS total_citas,
                    SUM(CASE WHEN c.id_estado_cita = 4 THEN 1 ELSE 0 END)::integer AS completadas,
                    SUM(CASE WHEN c.id_estado_cita = 2 THEN 1 ELSE 0 END)::integer AS canceladas
                FROM {Config.SCHEMA}.t_sala s
                LEFT JOIN {Config.SCHEMA}.t_citas c ON c.id_sala = s.id_sala
                    AND (%s::timestamp IS NULL OR c.fecha_agendamiento >= %s::timestamp)
                    AND (%s::timestamp IS NULL OR c.fecha_agendamiento <= %s::timestamp)
                GROUP BY s.id_sala, s.nombre, s.tipo_sala, s.estado_sala
                ORDER BY total_citas DESC
            """
            rows = db.execute_query(query, (f_desde, f_desde, f_hasta, f_hasta), fetchall=True) or []
            return [{
                "id_sala": r[0],
                "nombre_sala": r[1],
                "tipo_sala": r[2],
                "estado_sala": r[3],
                "total_citas": r[4],
                "completadas": r[5],
                "canceladas": r[6]
            } for r in rows]
        elif tipo == 'servicios':
            query = f"""
                SELECT 
                    srv.id_servicio, srv.nombre AS nombre_servicio, srv.precio_sugerido::double precision,
                    COUNT(cs.id_cita_servicio)::integer AS total_solicitudes,
                    COALESCE(SUM(cs.precio), 0)::double precision AS ingresos_estimados
                FROM {Config.SCHEMA}.t_servicio srv
                LEFT JOIN {Config.SCHEMA}.t_cita_servicio cs ON cs.id_servicio = srv.id_servicio
                LEFT JOIN {Config.SCHEMA}.t_citas c ON c.id_cita = cs.id_cita
                    AND (%s::timestamp IS NULL OR c.fecha_agendamiento >= %s::timestamp)
                    AND (%s::timestamp IS NULL OR c.fecha_agendamiento <= %s::timestamp)
                GROUP BY srv.id_servicio, srv.nombre, srv.precio_sugerido
                ORDER BY total_solicitudes DESC
            """
            rows = db.execute_query(query, (f_desde, f_desde, f_hasta, f_hasta), fetchall=True) or []
            return [{
                "id_servicio": r[0],
                "nombre_servicio": r[1],
                "precio_sugerido": r[2],
                "total_solicitudes": r[3],
                "ingresos_estimados": r[4]
            } for r in rows]
        else:
            query = f"""
                SELECT 
                    p.id_procedimiento, p.descripcion,
                    COALESCE(SUM(cs.precio), 0)::double precision AS ingresos_estimados
                FROM {Config.SCHEMA}.t_procedimiento p
                LEFT JOIN {Config.SCHEMA}.t_citas c ON c.id_procedimiento = p.id_procedimiento
                    AND (%s::timestamp IS NULL OR c.fecha_agendamiento >= %s::timestamp)
                    AND (%s::timestamp IS NULL OR c.fecha_agendamiento <= %s::timestamp)
                LEFT JOIN {Config.SCHEMA}.t_cita_servicio cs ON cs.id_cita = c.id_cita
                GROUP BY p.id_procedimiento, p.descripcion
                ORDER BY ingresos_estimados DESC
            """
            rows = db.execute_query(query, (f_desde, f_desde, f_hasta, f_hasta), fetchall=True) or []
            return [{
                "id_procedimiento": r[0],
                "descripcion": r[1],
                "ingresos_estimados": r[2]
            } for r in rows]
    except Exception as e:
        print(f"Error querying admin data: {str(e)}")
        return []

def reporte_administracion(para_list=None, is_manual=False, f_inicio='', f_fin='', tipo='salas'):
    try:
        if not para_list:
            para_list = []
        data_list = query_administration_data(tipo, f_inicio, f_fin)
        fecha_str = f"{f_inicio} a {f_fin}" if (f_inicio or f_fin) else date.today().strftime('%d/%m/%Y')
        desc = obtener_descripcion_reporte('administracion', tipo)
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #2A5C4D;">Reporte Administrativo - Clínica Alba</h2>
            <p>Se adjunta el reporte detallado: <strong>{desc}</strong>.</p>
            <p><strong>Periodo:</strong> {fecha_str}</p>
            <p>Saludos cordiales,<br>Administración Clínica Alba</p>
        </body>
        </html>
        """
        
        pdf_b64 = generate_administration_pdf(data_list, f"REPORTE: {desc.upper()} ({fecha_str})", tipo)
        
        import base64
        if tipo == 'salas':
            csv_lines = ["ID Sala;Nombre Sala;Tipo;Estado;Total Citas;Completadas;Canceladas"]
            for item in data_list:
                csv_lines.append(f"{item['id_sala']};{item['nombre_sala']};{item['tipo_sala']};{item['estado_sala']};{item['total_citas']};{item['completadas']};{item['canceladas']}")
        elif tipo == 'servicios':
            csv_lines = ["ID Servicio;Nombre Servicio;Precio Sugerido (BOB);Total Solicitudes;Ingresos Estimados (BOB)"]
            for item in data_list:
                csv_lines.append(f"{item['id_servicio']};{item['nombre_servicio']};{item['precio_sugerido']:.2f};{item['total_solicitudes']};{item['ingresos_estimados']:.2f}")
        else:
            csv_lines = ["ID Procedimiento;Descripcion;Ingresos Estimados (BOB)"]
            for item in data_list:
                csv_lines.append(f"{item['id_procedimiento']};{item['descripcion']};{item['ingresos_estimados']:.2f}")
                
        csv_content = "\uFEFF" + "\n".join(csv_lines)
        csv_b64 = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        
        attachments = [
            {
                "content": pdf_b64,
                "name": f"Reporte_Administracion_{tipo}_{fecha_str.replace('/', '-').replace(' ', '_')}.pdf"
            },
            {
                "content": csv_b64,
                "name": f"Detalle_Administracion_{tipo}_{fecha_str.replace('/', '-').replace(' ', '_')}.csv"
            }
        ]
        
        success = True
        for email in para_list:
            sent = send_email_brevo(email.strip(), f"Reporte Administrativo ({desc}) - Clínica Alba", html, attachments=attachments)
            if not sent:
                success = False
                
        if is_manual:
            if success:
                Bitacora.registrar("REPORTES", f"Envio_Manual_Admin_{tipo}", f"Enviado exitosamente a: {', '.join(para_list)} ({desc})")
                return True
            else:
                Bitacora.registrar("REPORTES", f"Envio_Manual_Admin_{tipo}_Fallido", f"Fallo al enviar a algunos destinatarios: {', '.join(para_list)}")
                return False
        return True
    except Exception as e:
        print(f"[SCHEDULER ERROR] Error in reporte_administracion: {str(e)}")
        if is_manual:
            Bitacora.registrar("REPORTES", f"Envio_Manual_Admin_{tipo}_Fallido", f"Excepción: {str(e)}")
        return False

def start_scheduler(app):
    """Inicia el hilo secundario del planificador."""
    t = threading.Thread(target=run_scheduler_loop, args=(app,), daemon=True)
    t.start()
