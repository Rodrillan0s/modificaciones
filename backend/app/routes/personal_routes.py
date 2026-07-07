from flask import Blueprint, request, jsonify
from ..config import db
from ..classes.security import admin_required, permission_required
from ..services.bitacora import Bitacora

personal_routes = Blueprint('personal_routes', __name__)

# =========================================================
# LISTAR PERSONAL
# =========================================================

@personal_routes.route('/api/personal', methods=['GET'])
@admin_required
@permission_required("visualizar_personal")
def listar_personal():
    try:

        query = """
           SELECT
        p.id_personal,
        pe.nombre,
        pe.ci,
        pe.telefono,
        pe.fecha_nacimiento,
        pe.direccion,
        pe.descripcion,
        p.especialidad,
        p.id_contrato,
        p.id_cargo,
        c.tipo_cargo,
        p.estado
    FROM clinica.t_personal p
    INNER JOIN clinica.t_persona pe
        ON pe.id_persona = p.id_personal
    INNER JOIN clinica.t_cargo c
        ON c.id_cargo = p.id_cargo
    ORDER BY pe.nombre
        """

        rows = db.execute_query(query, fetchall=True)

        data = [{
    "id_personal": r[0],
    "nombre": r[1],
    "ci": r[2],
    "telefono": r[3],
    "fecha_nacimiento": r[4],
    "direccion": r[5],
    "descripcion": r[6],
    "especialidad": r[7],
    "id_contrato": r[8],
    "id_cargo": r[9],
    "cargo": r[10],
    "estado": r[11]
} for r in (rows or [])]

        return jsonify({
            "success": True,
            "data": data
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# CREAR PERSONAL
# =========================================================

@personal_routes.route('/api/personal', methods=['POST'])
@admin_required
@permission_required("crear_personal")
def crear_personal():

    try:

        data = request.get_json() or {}

        nombre = data.get("nombre")
        telefono = data.get("telefono")
        fecha_nacimiento = data.get("fecha_nacimiento")
        direccion = data.get("direccion")
        ci = data.get("ci")
        descripcion = data.get("descripcion")

        especialidad = data.get("especialidad")
        id_contrato = data.get("id_contrato")
        id_cargo = data.get("id_cargo")

        if not all([
            nombre,
            fecha_nacimiento,
            ci,
            id_contrato,
            id_cargo
        ]):
            return jsonify({
                "success": False,
                "message": "Datos incompletos"
            }), 400

        sql = f"""
            CALL clinica.p_crear_personal(
                %s,%s,%s,%s,%s,%s,%s,%s,%s
            )
        """

        params = (
            nombre,
            telefono,
            fecha_nacimiento,
            direccion,
            ci,
            descripcion,
            especialidad,
            id_contrato,
            id_cargo
        )

        db.execute_query(
            sql,
            params,
            commit=True
        )

        Bitacora.registrar(
            "PERSONAL",
            "CREATE",
            f"Personal creado: {nombre}"
        )

        return jsonify({
            "success": True,
            "message": "Personal registrado correctamente"
        }), 201

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# =========================================================
# ACTUALIZAR PERSONAL
# =========================================================

@personal_routes.route('/api/personal/<int:id_personal>', methods=['PUT'])
@admin_required
@permission_required("modificar_personal")
def modificar_personal(id_personal):

    try:

        data = request.get_json() or {}

        sql = f"""
            CALL clinica.p_actualizar_personal(
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )
        """

        params = (
            id_personal,
            data.get("nombre"),
            data.get("telefono"),
            data.get("fecha_nacimiento"),
            data.get("direccion"),
            data.get("ci"),
            data.get("descripcion"),
            data.get("especialidad"),
            data.get("id_contrato"),
            data.get("estado"),
            data.get("id_cargo")
        )

        db.execute_query(
            sql,
            params,
            commit=True
        )

        Bitacora.registrar(
            "PERSONAL",
            "UPDATE",
            f"Personal actualizado {id_personal}"
        )

        return jsonify({
            "success": True,
            "message": "Personal actualizado"
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    
# =========================================================
# DESACTIVAR PERSONAL
# =========================================================

@personal_routes.route('/api/personal/<int:id_personal>', methods=['DELETE'])
@admin_required
@permission_required("dar_baja_personal")
def eliminar_personal(id_personal):

    try:

        db.execute_query("""
            UPDATE clinica.t_personal
            SET estado = 'INACTIVO'
            WHERE id_personal = %s
        """, (id_personal,), commit=True)

        Bitacora.registrar(
            "PERSONAL",
            "DELETE",
            f"Personal desactivado {id_personal}"
        )

        return jsonify({
            "success": True,
            "message": "Personal desactivado correctamente"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# LISTAR CARGOS
# =========================================================

@personal_routes.route('/api/cargos', methods=['GET'])
@admin_required
@permission_required("visualizar_personal")
def listar_cargos():

    try:

        rows = db.execute_query("""
            SELECT
                id_cargo,
                tipo_cargo
            FROM clinica.t_cargo
            ORDER BY tipo_cargo
        """, fetchall=True)

        data = [{
            "id_cargo": r[0],
            "cargo": r[1]
        } for r in (rows or [])]

        return jsonify({
            "success": True,
            "data": data
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# LISTAR CONTRATOS
# =========================================================

@personal_routes.route('/api/contratos', methods=['GET'])
@admin_required
@permission_required("visualizar_personal")
def listar_contratos():

    try:

        rows = db.execute_query("""
            SELECT
                id_contrato,
                tipo_contrato,
                fecha_contrato,
                fecha_fin_contrato,
                estado_contrato
            FROM clinica.t_contrato
            ORDER BY id_contrato
        """, fetchall=True)

        data = [{
            "id_contrato": r[0],
            "tipo_contrato": r[1],
            "fecha_contrato": r[2],
            "fecha_fin_contrato": r[3],
            "estado": r[4]
        } for r in (rows or [])]

        return jsonify({
            "success": True,
            "data": data
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500




# =========================================================
# LISTAR DISPONIBILIDAD DEL PERSONAL
# =========================================================

@personal_routes.route('/api/disponibilidad', methods=['GET'])
@admin_required
@permission_required("visualizar_personal")
def listar_disponibilidad():

    try:

        rows = db.execute_query("""
            SELECT
                d.id_disponibilidad,
                d.id_personal,
                pe.nombre,
                d.fecha_inicio::date,
                d.fecha_fin::Date,
                d.fecha_registro,
                d.motivo,
                d.observacion
            FROM clinica.t_disponibilidad_personal d
            INNER JOIN clinica.t_personal p
                ON p.id_personal = d.id_personal
            INNER JOIN clinica.t_persona pe
                ON pe.id_persona = p.id_personal
            ORDER BY d.fecha_inicio DESC
        """, fetchall=True)

        data = [{
            "id_disponibilidad": r[0],
            "id_personal": r[1],
            "nombre": r[2],
            "fecha_inicio": r[3],
            "fecha_fin": r[4],
            "fecha_registro": r[5],
            "motivo": r[6],
            "observacion": r[7]
        } for r in (rows or [])]

        return jsonify({
            "success": True,
            "data": data
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =========================================================
# REGISTRAR DISPONIBILIDAD
# =========================================================

@personal_routes.route('/api/disponibilidad', methods=['POST'])
@admin_required
@permission_required("modificar_personal")
def registrar_disponibilidad():

    try:

        data = request.get_json() or {}

        id_personal = data.get("id_personal")
        fecha_inicio = data.get("fecha_inicio")
        fecha_fin = data.get("fecha_fin")
        motivo = data.get("motivo")
        observacion = data.get("observacion")

        if not all([id_personal, fecha_inicio, fecha_fin, motivo]):

            return jsonify({
                "success": False,
                "message": "Datos incompletos."
            }), 400

        if fecha_inicio > fecha_fin:

            return jsonify({
                "success": False,
                "message": "La fecha inicio no puede ser mayor a la fecha fin."
            }), 400

        existe = db.execute_query("""
            SELECT 1
            FROM clinica.t_disponibilidad_personal
            WHERE id_personal = %s
            AND (
                    %s BETWEEN fecha_inicio AND fecha_fin
                OR  %s BETWEEN fecha_inicio AND fecha_fin
                OR  fecha_inicio BETWEEN %s AND %s
                OR  fecha_fin BETWEEN %s AND %s
            )
            LIMIT 1
        """,
        (
            id_personal,
            fecha_inicio,
            fecha_fin,
            fecha_inicio,
            fecha_fin,
            fecha_inicio,
            fecha_fin
        ),
        fetchone=True)

        if existe:

            return jsonify({
                "success": False,
                "message": "Ya existe un periodo registrado para ese personal."
            }), 400

        db.execute_query("""
            INSERT INTO clinica.t_disponibilidad_personal
            (
                id_personal,
                fecha_inicio,
                fecha_fin,
                motivo,
                observacion
            )
            VALUES
            (
                %s,%s,%s,%s,%s
            )
        """,
        (
            id_personal,
            fecha_inicio,
            fecha_fin,
            motivo,
            observacion
        ),
        commit=True)

        Bitacora.registrar(
            "PERSONAL",
            "CREATE",
            f"Disponibilidad registrada para personal {id_personal}"
        )

        return jsonify({
            "success": True,
            "message": "Disponibilidad registrada correctamente."
        }), 201

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    

# =========================================================
# ACTUALIZAR DISPONIBILIDAD
# =========================================================

@personal_routes.route('/api/disponibilidad/<int:id_disponibilidad>', methods=['PUT'])
@admin_required
@permission_required("modificar_personal")
def actualizar_disponibilidad(id_disponibilidad):

    try:

        data = request.get_json() or {}

        id_personal = data.get("id_personal")
        fecha_inicio = data.get("fecha_inicio")
        fecha_fin = data.get("fecha_fin")
        motivo = data.get("motivo")
        observacion = data.get("observacion")

        if fecha_inicio > fecha_fin:

            return jsonify({
                "success": False,
                "message": "La fecha inicio no puede ser mayor a la fecha fin."
            }), 400

        existe = db.execute_query("""
            SELECT 1
            FROM clinica.t_disponibilidad_personal
            WHERE id_personal = %s
            AND id_disponibilidad <> %s
            AND (
                    %s BETWEEN fecha_inicio AND fecha_fin
                OR  %s BETWEEN fecha_inicio AND fecha_fin
                OR  fecha_inicio BETWEEN %s AND %s
                OR  fecha_fin BETWEEN %s AND %s
            )
            LIMIT 1
        """,
        (
            id_personal,
            id_disponibilidad,
            fecha_inicio,
            fecha_fin,
            fecha_inicio,
            fecha_fin,
            fecha_inicio,
            fecha_fin
        ),
        fetchone=True)

        if existe:

            return jsonify({
                "success": False,
                "message": "Ya existe otro periodo registrado."
            }), 400

        db.execute_query("""
            UPDATE clinica.t_disponibilidad_personal
            SET
                id_personal = %s,
                fecha_inicio = %s,
                fecha_fin = %s,
                motivo = %s,
                observacion = %s
            WHERE id_disponibilidad = %s
        """,
        (
            id_personal,
            fecha_inicio,
            fecha_fin,
            motivo,
            observacion,
            id_disponibilidad
        ),
        commit=True)

        Bitacora.registrar(
            "PERSONAL",
            "UPDATE",
            f"Disponibilidad actualizada {id_disponibilidad}"
        )

        return jsonify({
            "success": True,
            "message": "Disponibilidad actualizada."
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
# =========================================================
# ELIMINAR DISPONIBILIDAD
# =========================================================

@personal_routes.route('/api/disponibilidad/<int:id_disponibilidad>', methods=['DELETE'])
@admin_required
@permission_required("modificar_personal")
def eliminar_disponibilidad(id_disponibilidad):

    try:

        db.execute_query("""
            DELETE
            FROM clinica.t_disponibilidad_personal
            WHERE id_disponibilidad = %s
        """,
        (id_disponibilidad,),
        commit=True)

        Bitacora.registrar(
            "PERSONAL",
            "DELETE",
            f"Disponibilidad eliminada {id_disponibilidad}"
        )

        return jsonify({
            "success": True,
            "message": "Disponibilidad eliminada correctamente."
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500        