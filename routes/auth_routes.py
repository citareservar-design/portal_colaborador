import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, abort
from models.models import db, Empresa, Empleado, Reserva, Cliente
from datetime import date, datetime


# --- CONFIGURACIÓN DE RUTAS DE CARPETAS ---
base_path = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_path, '..', 'templates')
static_dir = os.path.join(base_path, '..', 'static')

auth_bp = Blueprint('auth', __name__, 
                    template_folder=template_dir, 
                    static_folder=static_dir)

# --- FUNCIONES DE APOYO ---

def obtener_empresa_activa():
    """Trae la empresa 01 por defecto para el portal"""
    return Empresa.query.get("01")

# --- RUTAS ---

@auth_bp.route('/')
def login_page():
    """Muestra la página de login con los datos de la empresa 01"""
    empresa = obtener_empresa_activa()
    if not empresa:
        return "Error: Empresa 01 no encontrada en la base de datos", 500
        
    return render_template('login.html', 
                           empresa_nombre=empresa.emp_razon_social, 
                           emp_id_db=empresa.emp_id)
    
    

@auth_bp.route('/login', methods=['POST'])
def login():
    """Procesa el ingreso por cédula con restricción de estado activo"""
    cedula_ingresada = request.form.get('cedula')
    
    if not cedula_ingresada:
        flash("Por favor ingresa tu número de cédula", "error")
        return redirect(url_for('auth.login_page'))

    # 1. Buscamos al empleado por su cédula
    empleado = Empleado.query.filter_by(empl_cedula=cedula_ingresada).first()
    
    # 2. Primera restricción: ¿Existe el empleado?
    if not empleado:
        flash("Empleado no encontrado o cédula incorrecta", "error")
        return redirect(url_for('auth.login_page'))

    # 3. Segunda restricción: ¿Está activo? (empl_activo == 0 es False)
    if not empleado.empl_activo:
        flash("Tu usuario está desactivado. Contacta al administrador", "error")
        # Registramos el intento fallido en consola por seguridad si quieres
        print(f"Intento de acceso denegado para empleado inactivo: {empleado.empl_nombre}")
        return redirect(url_for('auth.login_page'))

    # 4. Si pasa ambas, iniciamos sesión
    session['user_id'] = str(empleado.empl_cedula)
    session['user_nombre'] = empleado.empl_nombre
    session['emp_id'] = empleado.emp_id
    
    return redirect(url_for('auth.dashboard'))




@auth_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    
    # Buscamos al empleado por su cédula guardada en sesión
    empleado = Empleado.query.filter_by(empl_cedula=session.get('user_id')).first()
    
    if not empleado:
        return "Error: Empleado no encontrado", 404

    # 1. Citas que faltan por atender (QUITAMOS el filtro de fecha para pruebas)
    # Así te mostrará la cita del 2 de marzo como pendiente
    citas_pendientes = Reserva.query.filter(
        Reserva.empl_id == empleado.empl_id,
        Reserva.res_estado.in_(['pendiente', 'confirmada', 'confirmado']) # Agregamos variantes por si acaso
    ).count()

    # 2. Citas que ya terminó
    citas_completadas = Reserva.query.filter(
        Reserva.empl_id == empleado.empl_id,
        Reserva.res_estado.in_(['finalizada', 'completada', 'finalizado'])
    ).count()

    # 3. Total
    total_dia = citas_pendientes + citas_completadas

    # DEBUG: Esto saldrá en tu terminal negra para que verifiques los datos
    print(f"DEBUG: Empleado ID: {empleado.empl_id} | Pendientes: {citas_pendientes} | Completadas: {citas_completadas}")

    # Lógica del saludo
    hora_actual = datetime.now().hour
    if 5 <= hora_actual < 12:
        saludo = "Buenos días"
    elif 12 <= hora_actual < 18:
        saludo = "Buenas tardes"
    else:
        saludo = "Buenas noches"
    
    return render_template('dashboard.html', 
                           saludo=saludo,
                           pendientes=citas_pendientes,
                           completadas=citas_completadas,
                           total=total_dia,
                           colaborador_nombre=empleado.empl_nombre,
                           colaborador_cedula=int(empleado.empl_cedula),
                           emp_id_db=session.get('emp_id'))

@auth_bp.route('/logout')
def logout():
    """Cierra la sesión y limpia las cookies"""
    session.clear()
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/banner_empresa/<emp_id>')
def servir_banner(emp_id):
    """Sirve la imagen de fondo desde la ruta de recursos de la empresa"""
    empresa = Empresa.query.get(emp_id)
    if not empresa or not empresa.emp_ruta_recursos:
        print(f"DEBUG: Empresa {emp_id} no encontrada o sin ruta de recursos")
        abort(404)

    # Construimos la ruta hacia la carpeta portalcolaboradores
    carpeta_banner = os.path.join(empresa.emp_ruta_recursos, 'portalcolaboradores')
    nombre_archivo = f"{empresa.emp_nit}.jpg"
    
    ruta_completa = os.path.join(carpeta_banner, nombre_archivo)
    
    # Debug en consola para verificar rutas físicas
    print(f"----------------------------------------------")
    print(f"DEBUG: Buscando imagen en: {ruta_completa}")
    print(f"DEBUG: ¿El archivo existe?: {os.path.exists(ruta_completa)}")
    print(f"----------------------------------------------")

    if not os.path.exists(ruta_completa):
        abort(404)

    return send_from_directory(carpeta_banner, nombre_archivo)





from datetime import date, timedelta

@auth_bp.route('/mis-reservas')
def mis_reservas():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    
    empleado = Empleado.query.filter_by(empl_cedula=session['user_id']).first()
    
    # Consulta base
    citas = db.session.query(Reserva, Cliente).join(
        Cliente, Reserva.cli_id == Cliente.cli_id
    ).filter(
        Reserva.empl_id == empleado.empl_id,
        Reserva.res_estado.in_(['pendiente', 'confirmada'])
    ).order_by(Reserva.res_fecha.asc(), Reserva.res_hora.asc()).all()

    # Clasificación por fechas
    hoy = date.today()
    manana = hoy + timedelta(days=1)
    
    agenda_agrupada = {
        'hoy': [],
        'manana': [],
        'futuro': []
    }

    for res, cli in citas:
        if res.res_fecha == hoy:
            agenda_agrupada['hoy'].append((res, cli))
        elif res.res_fecha == manana:
            agenda_agrupada['manana'].append((res, cli))
        else:
            agenda_agrupada['futuro'].append((res, cli))
    
    return render_template('reservas.html', 
                           agenda=agenda_agrupada,
                           total_citas=len(citas),
                           colaborador_nombre=empleado.empl_nombre,
                           emp_id_db=session.get('emp_id'))
    
    
@auth_bp.route('/foto_empleado/<empl_cedula>')
def servir_foto_empleado(empl_cedula):
    if 'user_id' not in session:
        abort(401)
        
    empleado = Empleado.query.filter_by(empl_cedula=empl_cedula).first()
    empresa = Empresa.query.get(empleado.emp_id)
    
    if not empresa or not empresa.emp_ruta_recursos:
        abort(404)

    # Construcción de ruta compatible (Windows/Linux)
    # C:\Apps\cocoanails\empleados\1112792459\1112792459.jpg
    carpeta_empleado = os.path.join(
        empresa.emp_ruta_recursos, 
        'empleados', 
        str(int(empleado.empl_cedula)) # Convertimos a int para quitar .0 si es decimal
    )
    
    nombre_archivo = f"{int(empleado.empl_cedula)}.jpg"
    
    if not os.path.exists(os.path.join(carpeta_empleado, nombre_archivo)):
        # Si no tiene foto, podrías retornar una por defecto o error 404
        abort(404)
        
    return send_from_directory(carpeta_empleado, nombre_archivo)



@auth_bp.route('/historial-citas')
def historial_citas():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    
    empleado = Empleado.query.filter_by(empl_cedula=session['user_id']).first()
    
    # Traemos solo las finalizadas/completadas
    historico = db.session.query(Reserva, Cliente).join(
        Cliente, Reserva.cli_id == Cliente.cli_id
    ).filter(
        Reserva.empl_id == empleado.empl_id,
        Reserva.res_estado.in_(['finalizada', 'completada', 'finalizado'])
    ).order_by(Reserva.res_fecha.desc(), Reserva.res_hora.desc()).all()
    
    return render_template('historial.html', 
                           historico=historico,
                           colaborador_nombre=empleado.empl_nombre,
                           emp_id_db=session.get('emp_id'))
    
    




@auth_bp.route('/comisiones')
def comisiones():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    
    empleado = Empleado.query.filter_by(empl_cedula=session['user_id']).first()
    empresa = Empresa.query.get(session['emp_id'])
    
    recibos = []
    base_path = empresa.emp_ruta_recursos # C:\Apps\cocoanails
    
    # Ruta base de comisiones: .../comisiones/
    comisiones_path = os.path.join(base_path, 'comisiones')
    
    if os.path.exists(comisiones_path):
        # Listamos las carpetas de fechas (ej: 2026-02-25)
        for fecha_dir in os.listdir(comisiones_path):
            # Ruta a la carpeta de la cédula: .../comisiones/2026-02-25/1112792459
            cedula_path = os.path.join(comisiones_path, fecha_dir, str(int(empleado.empl_cedula)))
            
            if os.path.exists(cedula_path):
                for archivo in os.listdir(cedula_path):
                    if archivo.endswith('.pdf'):
                        recibos.append({
                            'fecha': fecha_dir,
                            'nombre': archivo,
                            'ruta_fecha': fecha_dir # Para el link
                        })
    
    # Ordenamos por fecha descendente (más recientes primero)
    recibos.sort(key=lambda x: x['fecha'], reverse=True)

    return render_template('comisiones.html', 
                           recibos=recibos, 
                           colaborador_nombre=empleado.empl_nombre)

@auth_bp.route('/abrir-recibo/<fecha>/<archivo>')
def abrir_recibo(fecha, archivo):
    if 'user_id' not in session: abort(401)
    
    empleado = Empleado.query.filter_by(empl_cedula=session['user_id']).first()
    empresa = Empresa.query.get(session['emp_id'])
    
    # Construcción de ruta segura multi-plataforma
    path_final = os.path.join(
        empresa.emp_ruta_recursos, 
        'comisiones', 
        fecha, 
        str(int(empleado.empl_cedula))
    )
    
    return send_from_directory(path_final, archivo)



from flask import session, render_template, abort
from sqlalchemy import text
# Asegúrate de importar 'db' desde donde esté definido (ej: from ..extensions import db)

@auth_bp.route('/mis-resenas')
def mis_resenas():
    # 1. Verificación de sesión manual (como tus otros def)
    if 'user_id' not in session: 
        abort(401)

    # 2. Obtenemos datos de la sesión
    cedula_usuario = session.get('user_id') 
    emp_id = session.get('emp_id')

    try:
        # 3. BUSCAMOS EL ID DEL EMPLEADO USANDO LA CÉDULA (SQL PURO)
        # Esto evita tener que importar "Empleado" y que falle la ruta
        sql_id = text("SELECT empl_id FROM EMPLEADOS WHERE empl_cedula = :cedula")
        res_id = db.session.execute(sql_id, {'cedula': cedula_usuario}).fetchone()

        if not res_id:
            return "No se encontró el colaborador con esa cédula", 404
        
        # El ID real es el primer valor (ej: 1)
        id_empleado_db = res_id[0]

        # 4. BUSCAMOS LAS RESEÑAS CON ESE ID
        sql_resenas = text("""
            SELECT res_cliente_nombre, res_puntuacion, res_comentario, res_fecha 
            FROM RESENAS 
            WHERE empl_id = :empl_id AND res_visible = 1
            ORDER BY res_fecha DESC
        """)
        
        resultado = db.session.execute(sql_resenas, {'empl_id': id_empleado_db})
        resenas = resultado.mappings().all()
        
        # 5. CÁLCULOS PARA EL TEMPLATE
        total_resenas = len(resenas)
        promedio = sum(r['res_puntuacion'] for r in resenas) / total_resenas if total_resenas > 0 else 0

        # Esto imprimirá en tu terminal para que verifiques si encuentra los datos
        print(f"DEBUG: Cédula {cedula_usuario} tiene el ID {id_empleado_db}. Reseñas: {total_resenas}")

        return render_template('resenas.html', 
                               resenas=resenas, 
                               promedio=round(promedio, 1), 
                               total=total_resenas,
                               emp_id_db=emp_id)
                               
    except Exception as e:
        # Si algo falla, lo vemos en la consola
        print(f"Error en la consulta: {e}")
        abort(500)