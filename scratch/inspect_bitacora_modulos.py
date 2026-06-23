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
    SELECT modulo, COUNT(*)
    FROM clinica.t_bitacora
    GROUP BY modulo
    ORDER BY count DESC;
""")
print("--- Existing modulos in t_bitacora ---")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.close()
conn.close()
