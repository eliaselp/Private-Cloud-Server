# app/__init__.py
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
import logging
from logging.handlers import RotatingFileHandler

from config import Config
from .models import db, User, SharedFolder

login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__, 
                instance_relative_config=True,
                template_folder='templates',
                static_folder='static')
    
    app.config.from_object(config_class)
    
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs(os.path.join(app.instance_path, 'logs'), exist_ok=True)
    except OSError:
        pass
    
    if not app.debug:
        file_handler = RotatingFileHandler(
            os.path.join(app.instance_path, 'logs', 'nube.log'),
            maxBytes=1024 * 1024,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Nube Privada startup')
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @login_manager.unauthorized_handler
    def unauthorized():
        return redirect(url_for('auth.login'))
    
    from .auth import auth_bp
    from .admin import admin_bp
    from .routes import main_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
    
    with app.app_context():
        for name, path in app.config['SHARED_FOLDERS'].items():
            if not SharedFolder.query.filter_by(name=name).first():
                folder = SharedFolder(
                    name=name,
                    path=path,
                    description=f'Carpeta compartida: {name}',
                    is_active=True,
                    allowed_roles='viewer,editor,admin'
                )
                db.session.add(folder)
        db.session.commit()
    
    return app