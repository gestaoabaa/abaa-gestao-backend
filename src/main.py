import os
import sys
from flask import Flask, send_from_directory
from flask_cors import CORS
from src.extensions import db # Importa o db do novo arquivo

# Adicione o diretório raiz do projeto ao path para que as importações funcionem
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 1. Crie o app
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# 2. Configure o app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave_secreta_padrao_muito_segura')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 3. Inicialize o db com o app
db.init_app(app)

# Habilitar CORS para todas as rotas
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 4. Importe os modelos e rotas APÓS a inicialização do db
# Isso resolve o problema de importação circular
from src.models.user import User
from src.routes.user import user_bp
from src.routes.student import student_bp
from src.routes.dance_class import dance_class_bp
from src.routes.payment import payment_bp
from src.routes.attendance import attendance_bp
from src.routes.dashboard import dashboard_bp
from src.routes.upload import upload_bp
from src.routes.admin import admin_bp

# 5. Registre blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(student_bp, url_prefix='/api')
app.register_blueprint(dance_class_bp, url_prefix='/api')
app.register_blueprint(payment_bp, url_prefix='/api')
app.register_blueprint(attendance_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/api')
app.register_blueprint(upload_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api")

# 6. Crie as tabelas do banco de dados (apenas se não existirem)
with app.app_context():
    db.create_all()

# 7. Rota para servir o frontend estático
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404
    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
