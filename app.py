import os
import locale
from flask import Flask
from dotenv import load_dotenv
from models.models import db
from routes.auth_routes import auth_bp

# 1. Configuración de Localización (Idioma)
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'spanish')
    except:
        pass # Si falla, usará el idioma por defecto sin romper la app

load_dotenv()

# 2. Rutas base
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')

# 3. CREACIÓN DE LA APP (Debe ir antes de los filtros)
app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=static_dir)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 4. FILTROS PERSONALIZADOS (Ahora sí, usando @app)
@app.template_filter('fecha_es')
def fecha_es(fecha):
    if not fecha: return ""
    meses = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    }
    # Retorna: 27 Feb, 2026
    return f"{fecha.day} {meses.get(fecha.month, '')}, {fecha.year}"

@app.template_filter('hora_es')
def hora_es(hora):
    if not hora: return ""
    
    # Extraemos hora y minuto manualmente para evitar fallos de strftime
    h = hora.hour
    m = hora.minute
    
    # Determinamos si es AM o PM
    periodo = "p. m." if h >= 12 else "a. m."
    
    # Convertimos formato 24h a 12h
    h_12 = h % 12
    if h_12 == 0: h_12 = 12
    
    # Retorna: 09:00 a. m.
    return f"{h_12:02d}:{m:02d} {periodo}"

# 5. Inicialización de DB y Blueprints
db.init_app(app)
app.register_blueprint(auth_bp)

if __name__ == '__main__':
    # host 0.0.0.0 para que sea accesible desde el celular en la misma red WiFi
    app.run(host='0.0.0.0', port=5004, debug=True)