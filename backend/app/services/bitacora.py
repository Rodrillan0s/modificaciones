import json
from flask import request
from ..config import db, Config

class Bitacora:
    @staticmethod
    def _obtener_ip():
        """Captura la IP real del cliente."""
        if request.headers.getlist("X-Forwarded-For"):
            return request.headers.getlist("X-Forwarded-For")[0].split(',')[0]
        return request.remote_addr

    @staticmethod
    def registrar(modulo, accion, descripcion, id_usuario=None, id_sesion=None):
        """Registra un evento de auditoría en la base de datos."""
        try:
            meta = json.dumps({"ip": Bitacora._obtener_ip()})
            sql = f"""
                INSERT INTO {Config.SCHEMA}.t_bitacora 
                (modulo, accion, descripcion, id_usuario, id_sesion, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (modulo, accion, descripcion, id_usuario, id_sesion, meta)
            db.execute_query(sql, params, commit=True)
        except Exception as e:
            print(f"--- ERROR CRÍTICO BITÁCORA --- {e}")

    @staticmethod
    def listar(filtros=None, page=1, limit=20):
        """Consulta el historial formateando la fecha a Día/Mes/Año con filtros y paginación."""
        filtros = filtros or {}
        query = f"""
            SELECT b.id_bitacora, p.nombre, b.modulo, b.accion, 
                   b.descripcion, b.fecha_registro, b.metadata, b.id_sesion, u.nombre_usuario
            FROM {Config.SCHEMA}.t_bitacora b
            LEFT JOIN {Config.SCHEMA}.t_usuario u ON b.id_usuario = u.id_usuario
            LEFT JOIN {Config.SCHEMA}.t_persona p ON u.id_persona = p.id_persona
            WHERE 1=1
        """
        params = []
        if filtros.get('nombre'):
            query += " AND (p.nombre ILIKE %s OR u.nombre_usuario ILIKE %s)"
            t = f"%{filtros['nombre']}%"; params.extend([t, t])
        
        if filtros.get('modulo'):
            modulo_mapping = {
                'CITAS': ['CITAS', 'CITAS_SERVICIOS'],
                'INVENTARIO': ['INVENTARIO'],
                'PAGOS': ['PAGOS', 'FINANZAS'],
                'SEGURIDAD': ['AUTH', 'LOGIN', 'LOGOUT', 'SECURITY', 'SECURIDAD'],
                'ADMINISTRACION': ['USUARIOS', 'PROCEDIMIENTOS', 'ODONTOGRAMA', 'CONSULTORIOS', 'PERSONAL', 'SERVICIOS', 'PACIENTE', 'ADMIN']
            }
            mapped_modulos = modulo_mapping.get(filtros['modulo'])
            if mapped_modulos:
                placeholders = ", ".join(["%s"] * len(mapped_modulos))
                query += f" AND b.modulo IN ({placeholders})"
                params.extend(mapped_modulos)
            else:
                query += " AND b.modulo = %s"
                params.append(filtros['modulo'])

        if filtros.get('fecha_inicio'):
            query += " AND b.fecha_registro >= %s"
            params.append(f"{filtros['fecha_inicio']} 00:00:00")
            
        if filtros.get('fecha_fin'):
            query += " AND b.fecha_registro <= %s"
            params.append(f"{filtros['fecha_fin']} 23:59:59")

        offset = (page - 1) * limit
        query += " ORDER BY b.fecha_registro DESC LIMIT %s OFFSET %s"
        params.extend([limit + 1, offset])
        
        res = db.execute_query(query, tuple(params), fetchall=True) or []
        
        has_more = False
        if len(res) > limit:
            has_more = True
            res = res[:limit]
        
        logs_list = [{
            'id': r[0],
            'usuario': r[1] or r[8] or 'SISTEMA',
            'modulo': r[2],
            'accion': r[3],
            'descripcion': r[4],
            # Formato configurado: Día/Mes/Año Hora:Minuto:Segundo
            'fecha': r[5].strftime('%d/%m/%Y %H:%M:%S') if r[5] else None,
            'metadata': r[6],
            'id_sesion': r[7]
        } for r in res]
        
        return logs_list, has_more