from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Cấu hình cơ sở dữ liệu
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/tuyendung?charset=utf8mb4'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'super-secret-key'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads', 'avatars')
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 

    # ⚙️ Cấu hình Flask-Mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'youremail@gmail.com'   
    app.config['MAIL_PASSWORD'] = 'your_app_password'    

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Khởi tạo các extension
    db.init_app(app)
    migrate.init_app(app, db)

    # Cấu hình Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Import models
    from app import models

    # Đăng ký blueprint
    from app.routes.main_routes import main_bp
    app.register_blueprint(main_bp)

    from app.routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    @app.context_processor
    def inject_request():
        from flask import request
        return dict(request=request)

    return app
