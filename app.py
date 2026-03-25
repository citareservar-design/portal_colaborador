import os
import sys
from flask import Flask
from models.models import db
from routes.auth_routes import auth_bp

def create_app_portal():
    app = Flask(__name__)

    # 1. LEER CLIENTE ACTIVO DEL SISTEMA
    # .upper() asegura que 'cocoanails' o 'COCOANAILS' funcionen igual
    cliente = os.environ.get('CLIENTE_ACTIVO', '').upper()

    if not cliente:
        print("❌ ERROR: La variable de entorno 'CLIENTE_ACTIVO' no está definida.")
        # En Windows/Desarrollo podrías poner un default para no romper la app
        if os.environ.get('FLASK_ENV') == 'production':
            sys.exit(1)
        cliente = 'DESARROLLO' 

    # 2. CONSTRUIR LLAVES DINÁMICAS
    # Busca DATABASE_URL_COCOANAILS, DATABASE_URL_SABRINA, etc.
    db_uri_key = f"DATABASE_URL_{cliente}"
    db_uri = os.environ.get(db_uri_key)

    if not db_uri:
        print(f"❌ ERROR: No se encontró la variable {db_uri_key} en el sistema.")
        if os.environ.get('FLASK_ENV') == 'production':
            sys.exit(1)
        # Fallback para desarrollo local
        db_uri = "sqlite:///local_test.db"

    # 3. CONFIGURACIÓN DE LA APP
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SECRET_KEY'] = os.environ.get(f'SECRET_KEY_{cliente}', 'secret_temporal_123')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_NAME'] = f'session_portal_{cliente.lower()}'

    # Inicializar Base de Datos y Rutas
    db.init_app(app)
    app.register_blueprint(auth_bp)

    return app

app = create_app_portal()

if __name__ == '__main__':
    # Ejecución compatible
    puerto = int(os.environ.get('PORT_PORTAL', 5004))
    app.run(host='0.0.0.0', port=puerto, debug=True)