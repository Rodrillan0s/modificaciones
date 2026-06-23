import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('backend/app/.env')

db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    dbname=db_name,
    user=db_user,
    password=db_password
)
cur = conn.cursor()

cur.execute("""
    SELECT pg_get_functiondef(p.oid)
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'clinica' AND p.proname = 'p_ajustar_inventario';
""")
row = cur.fetchone()
print("--- Definition of p_ajustar_inventario ---")
if row:
    print(row[0])
else:
    print("Not found")

cur.close()
conn.close()
