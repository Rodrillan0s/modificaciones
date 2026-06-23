from flask import Blueprint, request, jsonify, Response
import csv
from io import StringIO
from ..config import db, Config
from ..classes.security import admin_required, permission_required
from ..services.bitacora import Bitacora

reportes_routes = Blueprint('reportes_routes', __name__)

# Helper function copied from inventario_routes.py
def ejecutar_query_reporte_filtrado(tipo, expirable, estado, f_inicio, f_fin, params_extra):
    id_material = params_extra.get('id_material', '')
    id_proveedor = params_extra.get('id_proveedor', '')
    top = params_extra.get('top', '')
    dias_vencimiento = params_extra.get('dias', '')
    stock_min = params_extra.get('stock_min', '')
    stock_max = params_extra.get('stock_max', '')
    solo_stock = params_extra.get('solo_stock', 'false').lower() == 'true'
    fecha_limite = params_extra.get('fecha', '')

    # Formateo cronológico preventivo para el Reporte Estático o rangos
    fecha_procesada_fin = f_fin
    if tipo == 'estatico' and fecha_limite:
        fecha_procesada_fin = str(fecha_limite).replace("T", " ")
        if len(fecha_procesada_fin) == 16:
            fecha_procesada_fin += ":00"

    # Encabezados dinámicos que se acoplan reactivamente en la interfaz
    headers_map = {
        'general': ["ID", "Descripción", "Precio Compra (Bs.)", "Precio Venta (Bs.)", "Expirable", "Stock Actual", "Lotes Activos", "Costo Total Compra (Bs.)", "Costo Total Venta (Bs.)"],
        'mermas': ["ID", "Material", "Precio Catálogo", "Precio Venta", "Expirable", "Unidades Mermadas", "Nro. Incidentes", "Costo Pérdida Compra (Bs.)", "Costo Pérdida Venta (Bs.)"],
        'ingresos': ["ID", "Material", "Precio Catálogo", "Precio Venta", "Expirable", "Total Ingresado", "Nro. Entradas", "Valor Ingreso Compra (Bs.)", "Valor Ingreso Venta (Bs.)"],
        'vencimientos': ["Código Lote", "Descripción Material", "Precio Base", "Precio Venta", "Expirable", "Stock en Riesgo", "Fecha Vencimiento", "Valor Riesgo Compra (Bs.)", "Valor Riesgo Venta (Bs.)"],
        'estatico': ["ID", "Material Clínico", "Precio Catálogo (Bs.)", "Precio Venta (Bs.)", "Expirable", "Stock a la Fecha", "Movimientos", "Costo Histórico Compra (Bs.)", "Costo Histórico Venta (Bs.)"]
    }
    headers = headers_map.get(tipo, ["ID", "Descripción", "Precio Compra", "Precio Venta", "Expirable", "Métrica", "Conteo"])

    # Invocación directa a la función procedimental maestra de PostgreSQL
    query = f"""
        SELECT 
            id_insumo, nombre_insumo, precio_catalogo, es_expirable, 
            cantidad_unidades, conteo_lotes_o_incidentes, fecha_referencial, 
            origen_extra, costo_valorizado 
        FROM {Config.SCHEMA}.f_kardex_analitico_universal(
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    
    # Casteos sanitizados para evitar excepciones de tipo en el motor relacional
    params = (
        str(tipo),
        str(expirable),
        str(estado),
        str(f_inicio),
        str(fecha_procesada_fin),
        str(id_material),
        str(id_proveedor),
        str(dias_vencimiento),
        str(stock_min),
        str(stock_max),
        bool(solo_stock),
        int(top) if top else None
    )
    
    rows = db.execute_query(query, params, fetchall=True) or []
    return rows, headers


# =========================================================
# REPORTES DE INVENTARIO (Solo Admin)
# =========================================================
@reportes_routes.route('/api/reportes/inventario', methods=['GET'])
@admin_required
def obtener_datos_reporte_inventario():
    try:
        tipo = request.args.get('tipo', 'general')
        expirable = request.args.get('expirable', 'TODOS')
        estado = request.args.get('estado', 'todos')
        f_inicio = request.args.get('fecha_inicio', '')
        f_fin = request.args.get('fecha_fin', '')

        # Cargar los precios de venta de los materiales para mapear
        mat_query = f"SELECT UPPER(nombre_material), precio_venta FROM {Config.SCHEMA}.t_materiales"
        mat_rows = db.execute_query(mat_query, fetchall=True) or []
        precio_venta_lookup = {r[0].strip(): float(r[1]) if r[1] is not None else 0.0 for r in mat_rows}

        rows, columns = ejecutar_query_reporte_filtrado(tipo, expirable, estado, f_inicio, f_fin, request.args)
        
        data = []
        for r in rows:
            desc = r[1]
            p_compra = float(r[2])
            p_venta = precio_venta_lookup.get(desc.upper().strip() if desc else "", 0.0)
            metrica = int(r[4])
            costo_compra = float(r[8])
            costo_venta = float(metrica * p_venta)

            data.append({
                "id": r[0] if tipo != 'vencimientos' else f"LOTE #{r[0]}",
                "descripcion": desc,
                "precio": p_compra,
                "precio_venta": p_venta,
                "info_extra": r[7] if tipo in ['vencimientos', 'ingresos', 'mermas', 'estatico'] else ("SÍ" if r[3] else "NO"),
                "metrica_core": metrica,
                "conteo_lotes": int(r[5]),
                "fecha_ref": r[6],
                "costo_total": costo_compra,
                "costo_total_venta": costo_venta
            })

        return jsonify({"success": True, "columns": columns, "data": data}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@reportes_routes.route('/api/reportes/inventario/exportar', methods=['GET'])
@admin_required
def exportar_reporte_inventario_csv():
    try:
        tipo = request.args.get('tipo', 'general')
        expirable = request.args.get('expirable', 'TODOS')
        estado = request.args.get('estado', 'todos')
        f_inicio = request.args.get('fecha_inicio', '')
        f_fin = request.args.get('fecha_fin', '')
        fecha_corte_param = request.args.get('fecha', '')

        # Cargar los precios de venta de los materiales para mapear
        mat_query = f"SELECT UPPER(nombre_material), precio_venta FROM {Config.SCHEMA}.t_materiales"
        mat_rows = db.execute_query(mat_query, fetchall=True) or []
        precio_venta_lookup = {r[0].strip(): float(r[1]) if r[1] is not None else 0.0 for r in mat_rows}

        si = StringIO()
        cw = csv.writer(si, delimiter=';') 

        rows, headers = ejecutar_query_reporte_filtrado(tipo, expirable, estado, f_inicio, f_fin, request.args)
        cw.writerow([h.upper() for h in headers])

        for r in rows:
            desc = r[1]
            p_compra = float(r[2])
            p_venta = precio_venta_lookup.get(desc.upper().strip() if desc else "", 0.0)
            expirable_str = "SÍ" if r[3] else "NO"
            metrica = int(r[4])
            costo_compra = float(r[8])
            costo_venta = float(metrica * p_venta)

            if tipo == 'general':
                cw.writerow([r[0], desc, f"{p_compra:.2f}", f"{p_venta:.2f}", expirable_str, metrica, r[5], f"{costo_compra:.2f}", f"{costo_venta:.2f}"])
            elif tipo == 'mermas':
                cw.writerow([r[0], desc, f"{p_compra:.2f}", f"{p_venta:.2f}", expirable_str, f"-{metrica}", r[5], f"{costo_compra:.2f}", f"{costo_venta:.2f}"])
            elif tipo == 'ingresos':
                cw.writerow([r[0], desc, f"{p_compra:.2f}", f"{p_venta:.2f}", expirable_str, f"+{metrica}", r[5], f"{costo_compra:.2f}", f"{costo_venta:.2f}"])
            elif tipo == 'vencimientos':
                cw.writerow([f"LOTE #{r[0]}", desc, f"{p_compra:.2f}", f"{p_venta:.2f}", expirable_str, metrica, f'="{r[6]}"', f"{costo_compra:.2f}", f"{costo_venta:.2f}"])
            elif tipo == 'estatico':
                cw.writerow([r[0], desc, f"{p_compra:.2f}", f"{p_venta:.2f}", expirable_str, metrica, r[5], f"{costo_compra:.2f}", f"{costo_venta:.2f}"])

        filename = f"Reporte_{tipo.upper()}_{f_inicio or 'SNAP'}_AL_{f_fin or 'HISTORIAL'}.csv"
        if tipo == 'estatico':
            filename = f"Reporte_ESTATICO_CORTE_{fecha_corte_param.replace(':', '-') if fecha_corte_param else 'AHORA'}.csv"

        output = si.getvalue().encode('latin-1', errors='replace')
        return Response(output, mimetype="text/csv; charset=latin-1", headers={"Content-disposition": f"attachment; filename={filename}"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


# =========================================================
# REPORTE DE PACIENTES (Solo Admin)
# =========================================================
@reportes_routes.route('/api/reportes/pacientes', methods=['GET'])
@admin_required
def get_reporte_pacientes():
    try:
        fecha_desde = request.args.get('fecha_desde') or None
        fecha_hasta = request.args.get('fecha_hasta') or None
        nombre = request.args.get('nombre') or None
        if nombre:
            nombre = f"%{nombre}%"

        query = f"""
            SELECT 
                p.id_persona,
                p.nombre,
                p.ci,
                p.telefono,
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
        params = (fecha_desde, fecha_desde, fecha_hasta, fecha_hasta, nombre, nombre)
        results = db.execute_query(query, params, fetchall=True)

        data = []
        if results:
            for row in results:
                data.append({
                    "id_paciente": row[0],
                    "nombre": row[1],
                    "ci": row[2],
                    "telefono": row[3],
                    "total_citas": row[4],
                    "programadas": row[5],
                    "canceladas": row[6],
                    "reprogramadas": row[7],
                    "completadas": row[8],
                    "no_asistio": row[9],
                    "total_pagado": row[10],
                    "saldo_pendiente": row[11],
                    "ultima_cita": row[12].strftime("%Y-%m-%d %H:%M") if row[12] else None
                })
        
        # Calculate overall KPIs
        total_pacientes = len(data)
        pacientes_activos = sum(1 for p in data if p['completadas'] > 0)
        deuda_total = sum(p['saldo_pendiente'] for p in data)
        pagado_total = sum(p['total_pagado'] for p in data)
        
        return jsonify({
            "success": True,
            "data": data,
            "kpis": {
                "total_pacientes": total_pacientes,
                "pacientes_activos": pacientes_activos,
                "deuda_total": deuda_total,
                "pagado_total": pagado_total
            }
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


# =========================================================
# REPORTE FINANCIERO (Solo Admin)
# =========================================================
@reportes_routes.route('/api/reportes/finanzas', methods=['GET'])
@admin_required
def get_reporte_finanzas():
    try:
        fecha_desde = request.args.get('fecha_desde') or None
        fecha_hasta = request.args.get('fecha_hasta') or None

        # 1. Ingresos por método de pago
        query_metodos = f"""
            SELECT 
                COALESCE(metodo_pago, 'Sin definir') AS metodo_pago,
                COUNT(id_factura)::integer AS transacciones,
                SUM(monto_cancelado)::double precision AS total_recaudado
            FROM {Config.SCHEMA}.t_facturas
            WHERE (%s::timestamp IS NULL OR fecha_factura >= %s::timestamp)
              AND (%s::timestamp IS NULL OR fecha_factura <= %s::timestamp)
            GROUP BY metodo_pago
            ORDER BY total_recaudado DESC
        """
        res_metodos = db.execute_query(query_metodos, (fecha_desde, fecha_desde, fecha_hasta, fecha_hasta), fetchall=True) or []
        metodos_data = [{"metodo_pago": r[0], "transacciones": r[1], "total_recaudado": r[2]} for r in res_metodos]

        # 2. Evolución mensual de cobros
        query_mensual = f"""
            SELECT 
                EXTRACT(YEAR FROM fecha_factura)::integer AS anio,
                EXTRACT(MONTH FROM fecha_factura)::integer AS mes,
                COUNT(id_factura)::integer AS transacciones,
                SUM(monto_cancelado)::double precision AS total_recaudado
            FROM {Config.SCHEMA}.t_facturas
            WHERE (%s::timestamp IS NULL OR fecha_factura >= %s::timestamp)
              AND (%s::timestamp IS NULL OR fecha_factura <= %s::timestamp)
            GROUP BY EXTRACT(YEAR FROM fecha_factura), EXTRACT(MONTH FROM fecha_factura)
            ORDER BY anio DESC, mes DESC
        """
        res_mensual = db.execute_query(query_mensual, (fecha_desde, fecha_desde, fecha_hasta, fecha_hasta), fetchall=True) or []
        mensual_data = [{"anio": r[0], "mes": r[1], "transacciones": r[2], "total_recaudado": r[3]} for r in res_mensual]

        # 3. Estado de deudas (saldos)
        query_saldos = f"""
            SELECT 
                COUNT(id_saldo)::integer AS total_deudas,
                COALESCE(SUM(saldo_inicial), 0)::double precision AS total_saldo_inicial,
                COALESCE(SUM(saldo_actual), 0)::double precision AS total_saldo_actual,
                COALESCE(SUM(saldo_inicial - saldo_actual), 0)::double precision AS total_amortizado
            FROM {Config.SCHEMA}.t_saldo s
            LEFT JOIN {Config.SCHEMA}.t_citas c ON c.id_cita = s.id_cita
            WHERE (%s::timestamp IS NULL OR c.fecha_agendamiento >= %s::timestamp)
              AND (%s::timestamp IS NULL OR c.fecha_agendamiento <= %s::timestamp)
        """
        res_saldos = db.execute_query(query_saldos, (fecha_desde, fecha_desde, fecha_hasta, fecha_hasta), fetchone=True)
        saldos_data = {
            "total_deudas": res_saldos[0] if res_saldos else 0,
            "total_saldo_inicial": res_saldos[1] if res_saldos else 0.0,
            "total_saldo_actual": res_saldos[2] if res_saldos else 0.0,
            "total_amortizado": res_saldos[3] if res_saldos else 0.0
        }

        # 4. Ingresos por Odontólogo
        query_odontologos = f"""
            SELECT 
                per.nombre AS nombre_odontologo,
                COUNT(c.id_cita)::integer AS total_citas,
                COALESCE(SUM(f.monto_cancelado), 0)::double precision AS total_facturado
            FROM {Config.SCHEMA}.t_personal pers
            JOIN {Config.SCHEMA}.t_persona per ON pers.id_personal = per.id_persona
            LEFT JOIN {Config.SCHEMA}.t_citas c ON c.id_personal = pers.id_personal
                AND (%s::timestamp IS NULL OR c.fecha_agendamiento >= %s::timestamp)
                AND (%s::timestamp IS NULL OR c.fecha_agendamiento <= %s::timestamp)
            LEFT JOIN {Config.SCHEMA}.t_facturas f ON f.id_cita = c.id_cita
            WHERE pers.id_cargo = 2
            GROUP BY per.nombre
            ORDER BY total_facturado DESC
        """
        res_odontologos = db.execute_query(query_odontologos, (fecha_desde, fecha_desde, fecha_hasta, fecha_hasta), fetchall=True) or []
        odontologos_data = [{"nombre_odontologo": r[0], "total_citas": r[1], "total_facturado": r[2]} for r in res_odontologos]

        # 5. Ingresos por Procedimiento
        query_procedimientos_fin = f"""
            SELECT 
                p.descripcion AS nombre_procedimiento,
                COUNT(c.id_cita)::integer AS total_citas,
                COALESCE(SUM(f.monto_cancelado), 0)::double precision AS total_facturado
            FROM {Config.SCHEMA}.t_procedimiento p
            LEFT JOIN {Config.SCHEMA}.t_citas c ON c.id_procedimiento = p.id_procedimiento
                AND (%s::timestamp IS NULL OR c.fecha_agendamiento >= %s::timestamp)
                AND (%s::timestamp IS NULL OR c.fecha_agendamiento <= %s::timestamp)
            LEFT JOIN {Config.SCHEMA}.t_facturas f ON f.id_cita = c.id_cita
            GROUP BY p.descripcion
            ORDER BY total_facturado DESC
        """
        res_procedimientos_fin = db.execute_query(query_procedimientos_fin, (fecha_desde, fecha_desde, fecha_hasta, fecha_hasta), fetchall=True) or []
        procedimientos_fin_data = [{"nombre_procedimiento": r[0], "total_citas": r[1], "total_facturado": r[2]} for r in res_procedimientos_fin]

        # KPIs consolidado
        total_ingresos = sum(m['total_recaudado'] for m in metodos_data)
        
        return jsonify({
            "success": True,
            "metodos_pago": metodos_data,
            "evolucion_mensual": mensual_data,
            "saldos": saldos_data,
            "ingresos_odontologos": odontologos_data,
            "ingresos_procedimientos": procedimientos_fin_data,
            "kpis": {
                "total_ingresos": total_ingresos,
                "saldo_pendiente": saldos_data["total_saldo_actual"],
                "total_amortizado": saldos_data["total_amortizado"],
                "total_transacciones": sum(m['transacciones'] for m in metodos_data)
            }
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


# =========================================================
# REPORTE ADMINISTRATIVO (Solo Admin)
# =========================================================
@reportes_routes.route('/api/reportes/administracion', methods=['GET'])
@admin_required
def get_reporte_administracion():
    try:
        fecha_desde = request.args.get('fecha_desde') or None
        fecha_hasta = request.args.get('fecha_hasta') or None

        # 1. Consultorios (Salas)
        query_salas = f"""
            SELECT 
                s.id_sala,
                s.nombre AS nombre_sala,
                s.tipo_sala,
                s.estado_sala,
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
        res_salas = db.execute_query(query_salas, (fecha_desde, fecha_desde, fecha_hasta, fecha_hasta), fetchall=True) or []
        salas_data = [{
            "id_sala": r[0],
            "nombre_sala": r[1],
            "tipo_sala": r[2],
            "estado_sala": r[3],
            "total_citas": r[4],
            "completadas": r[5],
            "canceladas": r[6]
        } for r in res_salas]

        # 2. Servicios
        query_servicios = f"""
            SELECT 
                srv.id_servicio,
                srv.nombre AS nombre_servicio,
                srv.precio_sugerido::double precision,
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
        res_servicios = db.execute_query(query_servicios, (fecha_desde, fecha_desde, fecha_hasta, fecha_hasta), fetchall=True) or []
        servicios_data = [{
            "id_servicio": r[0],
            "nombre_servicio": r[1],
            "precio_sugerido": r[2],
            "total_solicitudes": r[3],
            "ingresos_estimados": r[4]
        } for r in res_servicios]

        # 3. Procedimientos
        query_procedimientos = f"""
            SELECT 
                p.id_procedimiento,
                p.descripcion AS nombre_procedimiento,
                p.precio::double precision,
                COUNT(c.id_cita)::integer AS total_solicitudes,
                COALESCE(SUM(p.precio), 0)::double precision AS ingresos_estimados
            FROM {Config.SCHEMA}.t_procedimiento p
            LEFT JOIN {Config.SCHEMA}.t_citas c ON c.id_procedimiento = p.id_procedimiento
                AND (%s::timestamp IS NULL OR c.fecha_agendamiento >= %s::timestamp)
                AND (%s::timestamp IS NULL OR c.fecha_agendamiento <= %s::timestamp)
            GROUP BY p.id_procedimiento, p.descripcion, p.precio
            ORDER BY total_solicitudes DESC
        """
        res_procedimientos = db.execute_query(query_procedimientos, (fecha_desde, fecha_desde, fecha_hasta, fecha_hasta), fetchall=True) or []
        procedimientos_data = [{
            "id_procedimiento": r[0],
            "nombre_procedimiento": r[1],
            "precio": r[2],
            "total_solicitudes": r[3],
            "ingresos_estimados": r[4]
        } for r in res_procedimientos]

        # 4. Personal de Apoyo
        query_personal = f"""
            SELECT 
                per.nombre AS nombre_personal,
                carg.tipo_cargo AS cargo,
                COUNT(c.id_cita)::integer AS citas_gestionadas
            FROM {Config.SCHEMA}.t_personal pers
            JOIN {Config.SCHEMA}.t_persona per ON pers.id_personal = per.id_persona
            JOIN {Config.SCHEMA}.t_cargo carg ON pers.id_cargo = carg.id_cargo
            LEFT JOIN {Config.SCHEMA}.t_citas c ON c.id_personal = pers.id_personal
                AND (%s::timestamp IS NULL OR c.fecha_agendamiento >= %s::timestamp)
                AND (%s::timestamp IS NULL OR c.fecha_agendamiento <= %s::timestamp)
            WHERE pers.id_cargo <> 2
            GROUP BY per.nombre, carg.tipo_cargo
            ORDER BY citas_gestionadas DESC
        """
        res_personal = db.execute_query(query_personal, (fecha_desde, fecha_desde, fecha_hasta, fecha_hasta), fetchall=True) or []
        personal_data = [{"nombre_personal": r[0], "cargo": r[1], "citas_gestionadas": r[2]} for r in res_personal]

        # KPIs
        total_salas_activas = sum(1 for s in salas_data if s['total_citas'] > 0)
        total_servicios_ingreso = sum(s['ingresos_estimados'] for s in servicios_data)
        total_procedimientos_ingreso = sum(p['ingresos_estimados'] for p in procedimientos_data)

        return jsonify({
            "success": True,
            "salas": salas_data,
            "servicios": servicios_data,
            "procedimientos": procedimientos_data,
            "personal": personal_data,
            "kpis": {
                "total_salas_activas": total_salas_activas,
                "total_servicios_ingreso": total_servicios_ingreso,
                "total_procedimientos_ingreso": total_procedimientos_ingreso,
                "total_servicios_solicitados": sum(s['total_solicitudes'] for s in servicios_data),
                "total_procedimientos_solicitados": sum(p['total_solicitudes'] for p in procedimientos_data)
            }
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
