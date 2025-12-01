import socket
import psycopg2


ip = socket.gethostbyname("db.aqpfuhcbqjnyfjocdfex.supabase.co")

conn = psycopg2.connect(
    host=ip,
    database="postgres",
    user="postgres",
    password="tafaravictor@2007",
    port="5432"
)

print("Connected!")





