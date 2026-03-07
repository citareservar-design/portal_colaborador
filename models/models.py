from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Empresa(db.Model):
    __tablename__ = 'EMPRESAS'
    emp_id = db.Column(db.String(2), primary_key=True)
    emp_razon_social = db.Column(db.String(60))
    emp_ruta_recursos = db.Column(db.String(255))
    emp_nit = db.Column(db.String(12))

class Empleado(db.Model):
    __tablename__ = 'EMPLEADOS'
    empl_id = db.Column(db.Integer, primary_key=True)
    empl_nombre = db.Column(db.String(100))
    empl_cedula = db.Column(db.Numeric(15, 0), unique=True)
    emp_id = db.Column(db.String(2), db.ForeignKey('EMPRESAS.emp_id'))
    empl_activo = db.Column(db.Boolean, default=True)
    
    
class Cliente(db.Model):
    __tablename__ = 'CLIENTES'
    cli_id = db.Column(db.Integer, primary_key=True)
    cli_nombre = db.Column(db.String(100), nullable=False)
    cli_alias = db.Column(db.String(50))
    cli_notas_personales = db.Column(db.Text)
    emp_id = db.Column(db.String(2), db.ForeignKey('EMPRESAS.emp_id'))

class Reserva(db.Model):
    __tablename__ = 'RESERVAS'
    res_id = db.Column(db.Integer, primary_key=True)
    res_fecha = db.Column(db.Date, nullable=False)
    res_hora = db.Column(db.Time, nullable=False)
    res_tipo_servicio = db.Column(db.String(100))
    res_estado = db.Column(db.String(20))
    # --- ESTA ES LA COLUMNA QUE TE FALTABA ---
    cli_id = db.Column(db.Integer, db.ForeignKey('CLIENTES.cli_id'), nullable=False)
    # ----------------------------------------
    empl_id = db.Column(db.Integer, db.ForeignKey('EMPLEADOS.empl_id'))
    emp_id = db.Column(db.String(2), db.ForeignKey('EMPRESAS.emp_id'))
    
    

class Resena(db.Model):
    __tablename__ = 'RESENAS'
    
    res_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    emp_id = db.Column(db.String(2), db.ForeignKey('EMPRESAS.emp_id'), nullable=False)
    empl_id = db.Column(db.Integer, db.ForeignKey('EMPLEADOS.empl_id'), nullable=True)
    
    res_cliente_nombre = db.Column(db.String(100), nullable=False, default='Anónimo')
    res_puntuacion = db.Column(db.Integer, nullable=False)
    res_comentario = db.Column(db.Text)
    res_fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    res_visible = db.Column(db.Integer, default=1) # Usamos Integer para el TinyInt(1)
    
    # Esta es la relación con la tabla de RESERVAS que ya tienes
    res_id_reserva = db.Column(db.String(50), db.ForeignKey('RESERVAS.res_id'), unique=True)

    # Opcional: Relaciones para acceder fácil a los datos
    # empleado = db.relationship('Empleado', backref='resenas')