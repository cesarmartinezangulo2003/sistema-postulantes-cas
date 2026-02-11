import os
import re
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, session, Response, send_file
import pytz

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "CAMBIA_ESTA_CLAVE_EN_PRODUCCION")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Zona horaria de Perú
TIMEZONE = pytz.timezone('America/Lima')

# ===============================
# CONFIGURACIÓN DE BASE DE DATOS
# ===============================
DATABASE_URL = os.getenv("DATABASE_URL")

# Detectar si estamos en Railway (PostgreSQL) o local (SQLite)
if DATABASE_URL and DATABASE_URL.startswith("postgres"):
    # PRODUCCIÓN: PostgreSQL en Railway
    import psycopg
    USE_POSTGRES = True
    print("🐘 Usando PostgreSQL (Railway)")
else:
    # DESARROLLO: SQLite local
    import sqlite3
    USE_POSTGRES = False
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "muni.db")
    print("💾 Usando SQLite (Local)")


def now_peru():
    """Retorna la fecha/hora actual en Perú"""
    return datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")


# ===============================
# DB helpers
# ===============================
def get_conn():
    """
    Conexión a base de datos (PostgreSQL en Railway, SQLite en local)
    """
    if USE_POSTGRES:
        # PostgreSQL
        conn = psycopg.connect(DATABASE_URL)
        return conn
    else:
        # SQLite
        conn = sqlite3.connect(DB_PATH, timeout=20.0)
        conn.row_factory = sqlite3.Row
        
        # OPTIMIZACIONES DE SQLITE
        conn.execute("PRAGMA journal_mode=WAL")       
        conn.execute("PRAGMA synchronous=NORMAL")    
        conn.execute("PRAGMA cache_size=10000")       
        conn.execute("PRAGMA temp_store=MEMORY")     
        
        return conn


def registrar_log(usuario, accion):
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            if USE_POSTGRES:
                cur.execute("""
                  INSERT INTO logs (fecha, usuario, accion)
                  VALUES (%s, %s, %s)
                """, (now_peru(), usuario, accion))
            else:
                cur.execute("""
                  INSERT INTO logs (fecha, usuario, accion)
                  VALUES (?, ?, ?)
                """, (now_peru(), usuario, accion))
            conn.commit()
    except Exception as e:
        print(f"Error al registrar log: {e}")


def ensure_column(conn, table, column, ddl):
    """Solo para SQLite - agregar columnas si no existen"""
    if not USE_POSTGRES:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in cur.fetchall()]
        if column not in cols:
            cur.execute(ddl)
            conn.commit()


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()

        if USE_POSTGRES:
            # ===============================
            # POSTGRESQL - TABLAS COMPLETAS
            # ===============================
            cur.execute("""
            CREATE TABLE IF NOT EXISTS postulantes (
              id SERIAL PRIMARY KEY,
              created_at TIMESTAMP NOT NULL,
              convocatoria TEXT NOT NULL,
              apellidos TEXT NOT NULL,
              nombres TEXT NOT NULL,
              tipo_documento TEXT NOT NULL,
              numero_documento TEXT NOT NULL,
              fecha_nacimiento TEXT NOT NULL,
              sexo TEXT NOT NULL,
              celular TEXT NOT NULL,
              correo TEXT NOT NULL,
              validado INTEGER NOT NULL DEFAULT 0,
              fuerzas_armadas TEXT,
              tiene_discapacidad TEXT,
              tipo_discapacidad TEXT,
              area TEXT,
              usuario_atendio TEXT,
              fecha_atencion TIMESTAMP,
              UNIQUE(numero_documento, tipo_documento)
            );
            """)
            
            cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
              id SERIAL PRIMARY KEY,
              username TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL,
              rol TEXT NOT NULL,
              activo INTEGER NOT NULL DEFAULT 1,
              created_at TIMESTAMP NOT NULL
            );
            """)
            
            cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
              id SERIAL PRIMARY KEY,
              fecha TIMESTAMP NOT NULL,
              usuario TEXT NOT NULL,
              accion TEXT NOT NULL
            );
            """)
            
            # Crear índices para PostgreSQL
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_usuario_atendio 
                ON postulantes(usuario_atendio)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_sexo 
                ON postulantes(sexo)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_convocatoria 
                ON postulantes(convocatoria)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_area 
                ON postulantes(area)
            """)
            
        else:
            # ===============================
            # SQLITE - CON MIGRACIONES
            # ===============================
            cur.execute("""
            CREATE TABLE IF NOT EXISTS postulantes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              convocatoria TEXT NOT NULL,
              apellidos TEXT NOT NULL,
              nombres TEXT NOT NULL,
              tipo_documento TEXT NOT NULL,
              numero_documento TEXT NOT NULL,
              fecha_nacimiento TEXT NOT NULL,
              sexo TEXT NOT NULL,
              celular TEXT NOT NULL,
              correo TEXT NOT NULL
            );
            """)
            
            ensure_column(conn, "postulantes", "validado",
                "ALTER TABLE postulantes ADD COLUMN validado INTEGER NOT NULL DEFAULT 0")
            ensure_column(conn, "postulantes", "fuerzas_armadas",
                "ALTER TABLE postulantes ADD COLUMN fuerzas_armadas TEXT")
            ensure_column(conn, "postulantes", "tiene_discapacidad",
                "ALTER TABLE postulantes ADD COLUMN tiene_discapacidad TEXT")
            ensure_column(conn, "postulantes", "tipo_discapacidad",
                "ALTER TABLE postulantes ADD COLUMN tipo_discapacidad TEXT")
            ensure_column(conn, "postulantes", "area",
                "ALTER TABLE postulantes ADD COLUMN area TEXT")
            ensure_column(conn, "postulantes", "usuario_atendio",
                "ALTER TABLE postulantes ADD COLUMN usuario_atendio TEXT")
            ensure_column(conn, "postulantes", "fecha_atencion",
                "ALTER TABLE postulantes ADD COLUMN fecha_atencion TEXT")
            
            cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL,
              rol TEXT NOT NULL,
              activo INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL
            );
            """)
            
            cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              fecha TEXT NOT NULL,
              usuario TEXT NOT NULL,
              accion TEXT NOT NULL
            );
            """)
        
        conn.commit()

        # Admin por defecto (funciona en ambas DB)
        cur.execute("SELECT id FROM usuarios WHERE username='admin'")
        if not cur.fetchone():
            if USE_POSTGRES:
                cur.execute("""
                  INSERT INTO usuarios (username, password, rol, activo, created_at)
                  VALUES ('admin', 'Admin2026@Muni!', 'admin', 1, %s)
                """, (now_peru(),))
            else:
                cur.execute("""
                  INSERT INTO usuarios (username, password, rol, activo, created_at)
                  VALUES ('admin', 'Admin2026@Muni!', 'admin', 1, ?)
                """, (now_peru(),))
            conn.commit()


def crear_indices():
    """
    Crear índices para SQLite (PostgreSQL los crea en init_db)
    """
    if not USE_POSTGRES:
        with get_conn() as conn:
            cur = conn.cursor()
            
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_documento_unico
                ON postulantes(numero_documento, tipo_documento)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_usuario_atendio 
                ON postulantes(usuario_atendio)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_sexo 
                ON postulantes(sexo)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_convocatoria 
                ON postulantes(convocatoria)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_area 
                ON postulantes(area)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_usuario_sexo 
                ON postulantes(usuario_atendio, sexo)
            """)
            
            conn.commit()


# Inicializar base de datos e índices
init_db()
crear_indices()

# ===============================
# WEB
# ===============================
@app.get("/")
def home():
    return render_template("Formulario.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("rol") == "admin":
        return redirect("/admin")
    if session.get("rol") == "usuario":
        return redirect("/usuario")

    if request.method == "POST":
        usuario = (request.form.get("usuario") or "").strip()
        password = (request.form.get("password") or "").strip()

        with get_conn() as conn:
            cur = conn.cursor()
            if USE_POSTGRES:
                cur.execute("""
                  SELECT username, rol FROM usuarios
                  WHERE username=%s AND password=%s AND activo=1
                """, (usuario, password))
            else:
                cur.execute("""
                  SELECT username, rol FROM usuarios
                  WHERE username=? AND password=? AND activo=1
                """, (usuario, password))
            row = cur.fetchone()

        if row:
            if USE_POSTGRES:
                session["usuario"] = row[0]
                session["rol"] = row[1]
                session["admin"] = row[1] == "admin"
                rol = row[1]
                username = row[0]
            else:
                session["usuario"] = row["username"]
                session["rol"] = row["rol"]
                session["admin"] = row["rol"] == "admin"
                rol = row["rol"]
                username = row["username"]

            if rol == "usuario":
                registrar_log(username, "Inicio de sesión")

            return redirect("/admin" if rol == "admin" else "/usuario")

        return render_template("Login.html", error="Credenciales incorrectas")

    return render_template("Login.html")


@app.get("/logout")
def logout():
    usuario = session.get("usuario", "Desconocido")
    rol = session.get("rol")
    
    if rol == "usuario":
        registrar_log(usuario, "Cerró sesión")
    
    session.clear()
    return redirect("/login")


@app.get("/admin")
def admin():
    if session.get("rol") != "admin":
        return redirect("/login")

    with get_conn() as conn:
        cur = conn.cursor()

        # POSTULANTES ATENDIDOS
        cur.execute("""
          SELECT id, area, convocatoria, apellidos, nombres, tipo_documento,
                 numero_documento, fecha_nacimiento, sexo, celular, correo,
                 fuerzas_armadas, tiene_discapacidad, tipo_discapacidad,
                 created_at, usuario_atendio, fecha_atencion
          FROM postulantes
          WHERE usuario_atendio IS NOT NULL
          ORDER BY fecha_atencion DESC
        """)
        postulantes_raw = cur.fetchall()

        # POSTULANTES PENDIENTES
        cur.execute("""
          SELECT id, area, convocatoria, apellidos, nombres, tipo_documento,
                 numero_documento, fecha_nacimiento, sexo, celular, correo,
                 fuerzas_armadas, tiene_discapacidad, tipo_discapacidad,
                 created_at
          FROM postulantes
          WHERE usuario_atendio IS NULL
          ORDER BY created_at DESC
        """)
        pendientes_raw = cur.fetchall()

        # USUARIOS
        cur.execute("""
          SELECT username, rol, activo AS estado
          FROM usuarios
        """)
        usuarios_raw = cur.fetchall()

        # LOGS
        cur.execute("""
          SELECT fecha, usuario, accion
          FROM logs
          ORDER BY id DESC
          LIMIT 100
        """)
        logs_raw = cur.fetchall()

    # Convertir a diccionarios (compatible con ambas DB)
    if USE_POSTGRES:
        postulantes = [dict(zip([
            'id', 'area', 'convocatoria', 'apellidos', 'nombres', 'tipo_documento',
            'numero_documento', 'fecha_nacimiento', 'sexo', 'celular', 'correo',
            'fuerzas_armadas', 'tiene_discapacidad', 'tipo_discapacidad',
            'created_at', 'usuario_atendio', 'fecha_atencion'
        ], row)) for row in postulantes_raw]
        
        postulantes_pendientes = [dict(zip([
            'id', 'area', 'convocatoria', 'apellidos', 'nombres', 'tipo_documento',
            'numero_documento', 'fecha_nacimiento', 'sexo', 'celular', 'correo',
            'fuerzas_armadas', 'tiene_discapacidad', 'tipo_discapacidad', 'created_at'
        ], row)) for row in pendientes_raw]
        
        usuarios = [dict(zip(['username', 'rol', 'estado'], row)) for row in usuarios_raw]
        logs = [dict(zip(['fecha', 'usuario', 'accion'], row)) for row in logs_raw]
    else:
        postulantes = postulantes_raw
        postulantes_pendientes = pendientes_raw
        usuarios = usuarios_raw
        logs = logs_raw

    return render_template(
        "admin.html",
        postulantes=postulantes,
        postulantes_pendientes=postulantes_pendientes,
        total_postulantes=len(postulantes),
        total_pendientes=len(postulantes_pendientes),
        usuarios=usuarios,
        usuario=session.get("usuario", "Admin"),
        logs=logs
    )


@app.get("/usuario")
def usuario_panel():
    if session.get("rol") != "usuario":
        return redirect("/login")
    
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
          SELECT id, area, convocatoria, apellidos, nombres, tipo_documento,
                 numero_documento, fecha_nacimiento, sexo, celular, correo,
                 fuerzas_armadas, tiene_discapacidad, tipo_discapacidad,
                 created_at
          FROM postulantes
          WHERE usuario_atendio IS NULL
          ORDER BY created_at DESC
        """)
        postulantes_raw = cur.fetchall()
    
    # Convertir a diccionarios
    if USE_POSTGRES:
        postulantes = [dict(zip([
            'id', 'area', 'convocatoria', 'apellidos', 'nombres', 'tipo_documento',
            'numero_documento', 'fecha_nacimiento', 'sexo', 'celular', 'correo',
            'fuerzas_armadas', 'tiene_discapacidad', 'tipo_discapacidad', 'created_at'
        ], row)) for row in postulantes_raw]
    else:
        postulantes = postulantes_raw
    
    return render_template(
        "usuario.html",
        usuario=session.get("usuario"),
        postulantes=postulantes
    )


# ===============================
# API
# ===============================
@app.get("/api/health")
def health():
    db_type = "postgresql" if USE_POSTGRES else "sqlite"
    return jsonify({"ok": True, "db": db_type})


@app.post("/api/verificar-postulante")
def verificar_postulante():
    data = request.get_json(silent=True) or {}
    numero_documento = (data.get("numero_documento") or "").strip()
    tipo_documento = (data.get("tipo_documento") or "").strip()
    
    if not numero_documento or not tipo_documento:
        return jsonify({"ok": False, "error": "Datos incompletos"}), 400
    
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            if USE_POSTGRES:
                cur.execute("""
                    SELECT convocatoria, area, apellidos, nombres, created_at
                    FROM postulantes
                    WHERE numero_documento = %s AND tipo_documento = %s
                    LIMIT 1
                """, (numero_documento, tipo_documento))
            else:
                cur.execute("""
                    SELECT convocatoria, area, apellidos, nombres, created_at
                    FROM postulantes
                    WHERE numero_documento = ? AND tipo_documento = ?
                    LIMIT 1
                """, (numero_documento, tipo_documento))
            
            resultado = cur.fetchone()
            
            if resultado:
                if USE_POSTGRES:
                    return jsonify({
                        "ok": True,
                        "existe": True,
                        "convocatoria": resultado[0],
                        "area": resultado[1],
                        "apellidos": resultado[2],
                        "nombres": resultado[3],
                        "fecha_registro": str(resultado[4])
                    }), 200
                else:
                    return jsonify({
                        "ok": True,
                        "existe": True,
                        "convocatoria": resultado["convocatoria"],
                        "area": resultado["area"],
                        "apellidos": resultado["apellidos"],
                        "nombres": resultado["nombres"],
                        "fecha_registro": resultado["created_at"]
                    }), 200
            else:
                return jsonify({"ok": True, "existe": False}), 200
                
    except Exception as e:
        print(f"❌ Error al verificar postulante: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/submit")
def submit():
    data = request.get_json(silent=True) or {}

    area = (data.get("area") or "").strip()
    convocatoria = (data.get("convocatoria") or "").strip()
    apellidos = (data.get("apellidos") or "").strip().upper()
    nombres = (data.get("nombres") or "").strip().upper()
    tipo_documento = (data.get("tipo_documento") or "").strip()
    numero_documento = (data.get("numero_documento") or "").strip()
    fecha_nacimiento = (data.get("fecha_nacimiento") or "").strip()
    sexo = (data.get("sexo") or "").strip()
    celular = (data.get("celular") or "").strip()
    correo = (data.get("correo") or "").strip()
    fuerzas_armadas = (data.get("fuerzas_armadas") or "").strip()
    tiene_discapacidad = (data.get("tiene_discapacidad") or "").strip()
    tipo_discapacidad = (data.get("tipo_discapacidad") or "").strip()

    if not all([area, convocatoria, apellidos, nombres, tipo_documento,
                numero_documento, fecha_nacimiento,
                sexo, celular, correo, fuerzas_armadas, tiene_discapacidad]):
        return jsonify({"ok": False, "error": "Completa todos los campos"}), 400

    if not EMAIL_RE.match(correo):
        return jsonify({"ok": False, "error": "Correo inválido"}), 400

    try:
        with get_conn() as conn:
            cur = conn.cursor()
            
            # Verificar si ya existe
            if USE_POSTGRES:
                cur.execute("""
                    SELECT convocatoria, area FROM postulantes
                    WHERE numero_documento = %s AND tipo_documento = %s
                    LIMIT 1
                """, (numero_documento, tipo_documento))
            else:
                cur.execute("""
                    SELECT convocatoria, area FROM postulantes
                    WHERE numero_documento = ? AND tipo_documento = ?
                    LIMIT 1
                """, (numero_documento, tipo_documento))
            
            existe = cur.fetchone()
            
            if existe:
                conv = existe[0] if USE_POSTGRES else existe['convocatoria']
                return jsonify({
                    "ok": False, 
                    "error": f"El {tipo_documento} {numero_documento} ya está registrado en: {conv}"
                }), 400
            
            # Insertar nuevo postulante
            if USE_POSTGRES:
                cur.execute("""
                  INSERT INTO postulantes
                  (created_at, area, convocatoria, apellidos, nombres, tipo_documento,
                   numero_documento, fecha_nacimiento, sexo, celular, correo,
                   fuerzas_armadas, tiene_discapacidad, tipo_discapacidad, validado)
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
                """, (
                    now_peru(), area, convocatoria, apellidos, nombres, tipo_documento,
                    numero_documento, fecha_nacimiento, sexo, celular, correo,
                    fuerzas_armadas, tiene_discapacidad, tipo_discapacidad
                ))
            else:
                cur.execute("""
                  INSERT INTO postulantes
                  (created_at, area, convocatoria, apellidos, nombres, tipo_documento,
                   numero_documento, fecha_nacimiento, sexo, celular, correo,
                   fuerzas_armadas, tiene_discapacidad, tipo_discapacidad, validado)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (
                    now_peru(), area, convocatoria, apellidos, nombres, tipo_documento,
                    numero_documento, fecha_nacimiento, sexo, celular, correo,
                    fuerzas_armadas, tiene_discapacidad, tipo_discapacidad
                ))
            conn.commit()
            
            print(f"✅ Postulante registrado: {apellidos}, {nombres} - {tipo_documento} {numero_documento}")

        return jsonify({"ok": True})

    except Exception as e:
        print(f"❌ Error al registrar: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/postulantes/nuevos")
def postulantes_nuevos():
    if not session.get("admin"):
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    after_id = request.args.get("after_id", 0, type=int)

    with get_conn() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("""
                SELECT id, area, convocatoria, apellidos, nombres, tipo_documento,
                       numero_documento, fecha_nacimiento, sexo, celular, correo,
                       fuerzas_armadas, tiene_discapacidad, tipo_discapacidad, created_at
                FROM postulantes
                WHERE id > %s
                ORDER BY id ASC
            """, (after_id,))
        else:
            cur.execute("""
                SELECT id, area, convocatoria, apellidos, nombres, tipo_documento,
                       numero_documento, fecha_nacimiento, sexo, celular, correo,
                       fuerzas_armadas, tiene_discapacidad, tipo_discapacidad, created_at
                FROM postulantes
                WHERE id > ?
                ORDER BY id ASC
            """, (after_id,))
        rows = cur.fetchall()

    if USE_POSTGRES:
        items = [dict(zip([
            'id', 'area', 'convocatoria', 'apellidos', 'nombres', 'tipo_documento',
            'numero_documento', 'fecha_nacimiento', 'sexo', 'celular', 'correo',
            'fuerzas_armadas', 'tiene_discapacidad', 'tipo_discapacidad', 'created_at'
        ], row)) for row in rows]
    else:
        items = [dict(r) for r in rows]

    return jsonify({"ok": True, "items": items})


@app.get("/api/postulantes/pendientes-nuevos")
def postulantes_pendientes_nuevos():
    if session.get("rol") != "usuario":
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    after_id = request.args.get("after_id", 0, type=int)

    with get_conn() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("""
                SELECT id, area, convocatoria, apellidos, nombres, tipo_documento,
                       numero_documento, fecha_nacimiento, sexo, celular, correo,
                       fuerzas_armadas, tiene_discapacidad, tipo_discapacidad, created_at
                FROM postulantes
                WHERE id > %s AND usuario_atendio IS NULL
                ORDER BY id ASC
            """, (after_id,))
        else:
            cur.execute("""
                SELECT id, area, convocatoria, apellidos, nombres, tipo_documento,
                       numero_documento, fecha_nacimiento, sexo, celular, correo,
                       fuerzas_armadas, tiene_discapacidad, tipo_discapacidad, created_at
                FROM postulantes
                WHERE id > ? AND usuario_atendio IS NULL
                ORDER BY id ASC
            """, (after_id,))
        rows = cur.fetchall()

    if USE_POSTGRES:
        items = [dict(zip([
            'id', 'area', 'convocatoria', 'apellidos', 'nombres', 'tipo_documento',
            'numero_documento', 'fecha_nacimiento', 'sexo', 'celular', 'correo',
            'fuerzas_armadas', 'tiene_discapacidad', 'tipo_discapacidad', 'created_at'
        ], row)) for row in rows]
    else:
        items = [dict(r) for r in rows]

    return jsonify({"ok": True, "items": items})


@app.get("/api/postulantes/atendidos-nuevos")
def postulantes_atendidos_nuevos():
    if session.get("rol") != "admin":
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    after_id = request.args.get("after_id", 0, type=int)

    with get_conn() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("""
                SELECT id, area, convocatoria, apellidos, nombres, tipo_documento,
                       numero_documento, fecha_nacimiento, sexo, celular, correo,
                       fuerzas_armadas, tiene_discapacidad, tipo_discapacidad,
                       created_at, usuario_atendio, fecha_atencion
                FROM postulantes
                WHERE id > %s AND usuario_atendio IS NOT NULL
                ORDER BY id ASC
            """, (after_id,))
        else:
            cur.execute("""
                SELECT id, area, convocatoria, apellidos, nombres, tipo_documento,
                       numero_documento, fecha_nacimiento, sexo, celular, correo,
                       fuerzas_armadas, tiene_discapacidad, tipo_discapacidad,
                       created_at, usuario_atendio, fecha_atencion
                FROM postulantes
                WHERE id > ? AND usuario_atendio IS NOT NULL
                ORDER BY id ASC
            """, (after_id,))
        rows = cur.fetchall()

    if USE_POSTGRES:
        items = [dict(zip([
            'id', 'area', 'convocatoria', 'apellidos', 'nombres', 'tipo_documento',
            'numero_documento', 'fecha_nacimiento', 'sexo', 'celular', 'correo',
            'fuerzas_armadas', 'tiene_discapacidad', 'tipo_discapacidad',
            'created_at', 'usuario_atendio', 'fecha_atencion'
        ], row)) for row in rows]
    else:
        items = [dict(r) for r in rows]

    return jsonify({"ok": True, "items": items})


@app.get("/api/postulantes/registrados")
def postulantes_registrados():
    if session.get("rol") != "admin":
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, area, convocatoria, apellidos, nombres, tipo_documento,
                   numero_documento, fecha_nacimiento, sexo, celular, correo,
                   fuerzas_armadas, tiene_discapacidad, tipo_discapacidad, created_at
            FROM postulantes
            WHERE usuario_atendio IS NULL
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()

    if USE_POSTGRES:
        items = [dict(zip([
            'id', 'area', 'convocatoria', 'apellidos', 'nombres', 'tipo_documento',
            'numero_documento', 'fecha_nacimiento', 'sexo', 'celular', 'correo',
            'fuerzas_armadas', 'tiene_discapacidad', 'tipo_discapacidad', 'created_at'
        ], row)) for row in rows]
    else:
        items = [dict(r) for r in rows]

    return jsonify({"ok": True, "items": items})


@app.get("/api/estadisticas")
def estadisticas():
    if session.get("rol") != "admin":
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    try:
        with get_conn() as conn:
            cur = conn.cursor()
            
            # Registrados mujeres
            cur.execute("""
                SELECT COUNT(*) as total
                FROM postulantes
                WHERE usuario_atendio IS NULL AND sexo = 'Femenino'
            """)
            registrados_mujeres = cur.fetchone()[0] if USE_POSTGRES else cur.fetchone()["total"]
            
            # Registrados hombres
            cur.execute("""
                SELECT COUNT(*) as total
                FROM postulantes
                WHERE usuario_atendio IS NULL AND sexo = 'Masculino'
            """)
            registrados_hombres = cur.fetchone()[0] if USE_POSTGRES else cur.fetchone()["total"]
            
            # Recibidos mujeres
            cur.execute("""
                SELECT COUNT(*) as total
                FROM postulantes
                WHERE usuario_atendio IS NOT NULL AND sexo = 'Femenino'
            """)
            recibidos_mujeres = cur.fetchone()[0] if USE_POSTGRES else cur.fetchone()["total"]
            
            # Recibidos hombres
            cur.execute("""
                SELECT COUNT(*) as total
                FROM postulantes
                WHERE usuario_atendio IS NOT NULL AND sexo = 'Masculino'
            """)
            recibidos_hombres = cur.fetchone()[0] if USE_POSTGRES else cur.fetchone()["total"]
            
            # Por área
            cur.execute("""
                SELECT area, COUNT(*) as total
                FROM postulantes
                WHERE area IS NOT NULL
                GROUP BY area
            """)
            rows_area = cur.fetchall()
            
            if USE_POSTGRES:
                por_area = {row[0]: row[1] for row in rows_area}
            else:
                por_area = {row["area"]: row["total"] for row in rows_area}
            
        return jsonify({
            "ok": True,
            "registrados_mujeres": registrados_mujeres,
            "registrados_hombres": registrados_hombres,
            "recibidos_mujeres": recibidos_mujeres,
            "recibidos_hombres": recibidos_hombres,
            "conv_barrido": 0,
            "conv_parques": 0,
            "conv_fiscalizacion": 0,
            "por_area": por_area
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/eliminar/<int:pid>")
def api_eliminar(pid):
    if session.get("rol") not in ["admin", "usuario"]:
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    with get_conn() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("DELETE FROM postulantes WHERE id=%s", (pid,))
        else:
            cur.execute("DELETE FROM postulantes WHERE id=?", (pid,))
        conn.commit()

    return jsonify({"ok": True})


# ===============================
# EXPORTACIONES
# ===============================
@app.get("/admin/export/csv")
def export_csv():
    if session.get("rol") != "admin":
        return redirect("/login")

    import csv
    from io import StringIO

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
          SELECT id, area, convocatoria, apellidos, nombres, tipo_documento,
                 numero_documento, fecha_nacimiento, sexo, celular, correo,
                 fuerzas_armadas, tiene_discapacidad, tipo_discapacidad,
                 created_at, usuario_atendio, fecha_atencion
          FROM postulantes
          WHERE usuario_atendio IS NOT NULL
          ORDER BY fecha_atencion DESC
        """)
        postulantes_raw = cur.fetchall()

    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'ID', 'Área', 'Convocatoria', 'Apellidos', 'Nombres', 'Tipo Doc', 'N° Doc',
        'Fecha Nacimiento', 'Sexo', 'Celular', 'Correo', 'FF.AA.', 
        'Discapacidad', 'Tipo Discapacidad', 'Fecha Registro',
        'Usuario Atendió', 'Fecha Atención'
    ])
    
    for p in postulantes_raw:
        if USE_POSTGRES:
            writer.writerow([
                p[0], p[1] or '', p[2], p[3], p[4], p[5], p[6], p[7], p[8],
                p[9], p[10], p[11], p[12], p[13] or '', str(p[14]), p[15], str(p[16])
            ])
        else:
            writer.writerow([
                p['id'], p['area'] or '', p['convocatoria'], p['apellidos'], p['nombres'],
                p['tipo_documento'], p['numero_documento'], p['fecha_nacimiento'],
                p['sexo'], p['celular'], p['correo'], p['fuerzas_armadas'],
                p['tiene_discapacidad'], p['tipo_discapacidad'] or '',
                p['created_at'], p['usuario_atendio'], p['fecha_atencion']
            ])

    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=postulantes_{datetime.now(TIMEZONE).strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@app.get("/admin/export/excel")
def export_excel():
    if session.get("rol") != "admin":
        return redirect("/login")

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from io import BytesIO
    except ImportError:
        return jsonify({
            "ok": False, 
            "error": "openpyxl no está instalado"
        }), 500

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
          SELECT id, area, convocatoria, apellidos, nombres, tipo_documento,
                 numero_documento, fecha_nacimiento, sexo, celular, correo,
                 fuerzas_armadas, tiene_discapacidad, tipo_discapacidad,
                 created_at, usuario_atendio, fecha_atencion
          FROM postulantes
          WHERE usuario_atendio IS NOT NULL
          ORDER BY fecha_atencion DESC
        """)
        postulantes_raw = cur.fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "Postulantes"

    header_fill = PatternFill(start_color="003f8f", end_color="003f8f", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    header_alignment = Alignment(horizontal="center", vertical="center")

    headers = [
        'ID', 'Área', 'Convocatoria', 'Apellidos', 'Nombres', 'Tipo Doc', 'N° Doc',
        'Fecha Nacimiento', 'Sexo', 'Celular', 'Correo', 'FF.AA.',
        'Discapacidad', 'Tipo Discapacidad', 'Fecha Registro',
        'Usuario Atendió', 'Fecha Atención'
    ]
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    for row_num, p in enumerate(postulantes_raw, 2):
        if USE_POSTGRES:
            ws.cell(row=row_num, column=1, value=p[0])
            ws.cell(row=row_num, column=2, value=p[1] or '')
            ws.cell(row=row_num, column=3, value=p[2])
            ws.cell(row=row_num, column=4, value=p[3])
            ws.cell(row=row_num, column=5, value=p[4])
            ws.cell(row=row_num, column=6, value=p[5])
            ws.cell(row=row_num, column=7, value=p[6])
            ws.cell(row=row_num, column=8, value=p[7])
            ws.cell(row=row_num, column=9, value=p[8])
            ws.cell(row=row_num, column=10, value=p[9])
            ws.cell(row=row_num, column=11, value=p[10])
            ws.cell(row=row_num, column=12, value=p[11])
            ws.cell(row=row_num, column=13, value=p[12])
            ws.cell(row=row_num, column=14, value=p[13] or '')
            ws.cell(row=row_num, column=15, value=str(p[14]))
            ws.cell(row=row_num, column=16, value=p[15])
            ws.cell(row=row_num, column=17, value=str(p[16]))
        else:
            ws.cell(row=row_num, column=1, value=p['id'])
            ws.cell(row=row_num, column=2, value=p['area'] or '')
            ws.cell(row=row_num, column=3, value=p['convocatoria'])
            ws.cell(row=row_num, column=4, value=p['apellidos'])
            ws.cell(row=row_num, column=5, value=p['nombres'])
            ws.cell(row=row_num, column=6, value=p['tipo_documento'])
            ws.cell(row=row_num, column=7, value=p['numero_documento'])
            ws.cell(row=row_num, column=8, value=p['fecha_nacimiento'])
            ws.cell(row=row_num, column=9, value=p['sexo'])
            ws.cell(row=row_num, column=10, value=p['celular'])
            ws.cell(row=row_num, column=11, value=p['correo'])
            ws.cell(row=row_num, column=12, value=p['fuerzas_armadas'])
            ws.cell(row=row_num, column=13, value=p['tiene_discapacidad'])
            ws.cell(row=row_num, column=14, value=p['tipo_discapacidad'] or '')
            ws.cell(row=row_num, column=15, value=p['created_at'])
            ws.cell(row=row_num, column=16, value=p['usuario_atendio'])
            ws.cell(row=row_num, column=17, value=p['fecha_atencion'])

    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"postulantes_{datetime.now(TIMEZONE).strftime('%Y%m%d_%H%M%S')}.xlsx"
    )


@app.post("/api/recibir-postulante")
def recibir_postulante():
    if session.get("rol") != "usuario":
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    data = request.get_json()
    postulante_id = data.get("id")

    if not postulante_id:
        return jsonify({"ok": False, "error": "ID no proporcionado"}), 400

    usuario_actual = session.get("usuario")
    fecha_actual = now_peru()

    try:
        with get_conn() as conn:
            cur = conn.cursor()
            
            if USE_POSTGRES:
                cur.execute("SELECT apellidos, nombres FROM postulantes WHERE id = %s", (postulante_id,))
            else:
                cur.execute("SELECT apellidos, nombres FROM postulantes WHERE id = ?", (postulante_id,))
            postulante = cur.fetchone()
            
            if USE_POSTGRES:
                cur.execute("""
                  UPDATE postulantes
                  SET usuario_atendio = %s, fecha_atencion = %s
                  WHERE id = %s AND usuario_atendio IS NULL
                """, (usuario_actual, fecha_actual, postulante_id))
            else:
                cur.execute("""
                  UPDATE postulantes
                  SET usuario_atendio = ?, fecha_atencion = ?
                  WHERE id = ? AND usuario_atendio IS NULL
                """, (usuario_actual, fecha_actual, postulante_id))
            conn.commit()

            if cur.rowcount == 0:
                return jsonify({"ok": False, "error": "Postulante ya fue atendido"}), 400

        if postulante:
            apellidos = postulante[0] if USE_POSTGRES else postulante['apellidos']
            nombres = postulante[1] if USE_POSTGRES else postulante['nombres']
            registrar_log(usuario_actual, f"Recibió a {apellidos}, {nombres}")
        else:
            registrar_log(usuario_actual, f"Recibió al postulante ID {postulante_id}")
        
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/activar-usuario")
def activar_usuario():
    if session.get("rol") != "admin":
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    data = request.get_json()
    username = data.get("username")

    with get_conn() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("UPDATE usuarios SET activo = 1 WHERE username = %s", (username,))
        else:
            cur.execute("UPDATE usuarios SET activo = 1 WHERE username = ?", (username,))
        conn.commit()

    return jsonify({"ok": True})


@app.post("/api/desactivar-usuario")
def desactivar_usuario():
    if session.get("rol") != "admin":
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    data = request.get_json()
    username = data.get("username")

    if username == "admin":
        return jsonify({"ok": False, "error": "No se puede desactivar admin"}), 400

    with get_conn() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("UPDATE usuarios SET activo = 0 WHERE username = %s", (username,))
        else:
            cur.execute("UPDATE usuarios SET activo = 0 WHERE username = ?", (username,))
        conn.commit()

    return jsonify({"ok": True})


@app.post("/api/crear-usuario")
def crear_usuario():
    if session.get("rol") != "admin":
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    rol = data.get("rol", "usuario")

    if not username or not password:
        return jsonify({"ok": False, "error": "Datos incompletos"}), 400

    try:
        with get_conn() as conn:
            cur = conn.cursor()
            if USE_POSTGRES:
                cur.execute("""
                  INSERT INTO usuarios (username, password, rol, activo, created_at)
                  VALUES (%s, %s, %s, 1, %s)
                """, (username, password, rol, now_peru()))
            else:
                cur.execute("""
                  INSERT INTO usuarios (username, password, rol, activo, created_at)
                  VALUES (?, ?, ?, 1, ?)
                """, (username, password, rol, now_peru()))
            conn.commit()
        
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/eliminar-usuario")
def eliminar_usuario():
    if session.get("rol") != "admin":
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    data = request.get_json()
    username = data.get("username", "").strip()

    if username == "admin":
        return jsonify({"ok": False, "error": "No se puede eliminar el usuario admin"}), 400

    if not username:
        return jsonify({"ok": False, "error": "Usuario no especificado"}), 400

    try:
        with get_conn() as conn:
            cur = conn.cursor()
            if USE_POSTGRES:
                cur.execute("DELETE FROM usuarios WHERE username = %s", (username,))
            else:
                cur.execute("DELETE FROM usuarios WHERE username = ?", (username,))
            conn.commit()

            if cur.rowcount == 0:
                return jsonify({"ok": False, "error": "Usuario no encontrado"}), 404

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/limpiar-logs")
def limpiar_logs():
    if session.get("rol") != "admin":
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM logs")
            eliminados = cur.rowcount
            conn.commit()

        return jsonify({"ok": True, "eliminados": eliminados})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/obtener-password")
def obtener_password():
    if session.get("rol") != "admin":
        return jsonify({"ok": False, "error": "No autorizado"}), 403

    data = request.get_json()
    username = data.get("username", "").strip()

    if not username:
        return jsonify({"ok": False, "error": "Usuario no especificado"}), 400

    try:
        with get_conn() as conn:
            cur = conn.cursor()
            if USE_POSTGRES:
                cur.execute("SELECT password FROM usuarios WHERE username = %s", (username,))
            else:
                cur.execute("SELECT password FROM usuarios WHERE username = ?", (username,))
            row = cur.fetchone()

            if not row:
                return jsonify({"ok": False, "error": "Usuario no encontrado"}), 404

        password = row[0] if USE_POSTGRES else row["password"]
        return jsonify({"ok": True, "password": password})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("="*70)
    print("🚀 SISTEMA DE REGISTRO DE POSTULANTES CAS 2026 - MML")
    print("="*70)
    print("✅ Validación de DNI único activada")
    print("✅ Campos APELLIDOS y NOMBRES separados en MAYÚSCULAS")
    if USE_POSTGRES:
        print("🐘 Base de datos: PostgreSQL (Railway)")
    else:
        print("💾 Base de datos: SQLite (Local)")
    print("🌐 Acceso: http://localhost:5000")
    print("="*70)
    app.run(debug=True)