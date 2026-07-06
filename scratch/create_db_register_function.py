import sys
import os

# Adjust path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.config import db, Config

sql_create_function = f"""
CREATE OR REPLACE FUNCTION {Config.SCHEMA}.f_registrar_asistencia(
    p_id_personal INT, 
    p_id_creador_qr INT
)
RETURNS TABLE (
    r_id_asistencia INT,
    r_tipo VARCHAR,
    r_fecha_registro TIMESTAMPTZ
) AS $$
DECLARE
    v_ultimo_tipo VARCHAR;
    v_tipo VARCHAR;
    v_ahora TIMESTAMPTZ := CURRENT_TIMESTAMP;
BEGIN
    -- 1. Buscar la última marca del día REAL local del usuario (forzando la zona horaria)
    -- Además usamos FOR UPDATE para bloquear temporalmente marcas concurrentes de este usuario
    SELECT tipo INTO v_ultimo_tipo
    FROM {Config.SCHEMA}.t_asistencia
    WHERE id_personal = p_id_personal 
      AND (fecha_registro AT TIME ZONE 'America/La_Paz')::DATE = (v_ahora AT TIME ZONE 'America/La_Paz')::DATE
    ORDER BY fecha_registro DESC
    LIMIT 1
    FOR UPDATE; 

    -- 2. Determinar el tipo de asistencia de forma fluida
    IF v_ultimo_tipo = 'ENTRADA' THEN
        v_tipo := 'SALIDA';
    ELSE
        v_tipo := 'ENTRADA';
    END IF;

    -- 3. Insertar la nueva marca con la hora exacta
    INSERT INTO {Config.SCHEMA}.t_asistencia (id_personal, id_creador_qr, tipo, fecha_registro)
    VALUES (p_id_personal, p_id_creador_qr, v_tipo, v_ahora)
    RETURNING id_asistencia, tipo, fecha_registro 
    INTO r_id_asistencia, r_tipo, r_fecha_registro;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;
"""

try:
    print("Creating f_registrar_asistencia database function (corrected timezone syntax)...")
    db.execute_query(sql_create_function, commit=True)
    print("Function created successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
