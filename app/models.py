# app/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='viewer')  # admin, editor, viewer
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_ip = db.Column(db.String(45))
    
    # Relaciones
    file_logs = db.relationship('FileLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def can_upload(self):
        return self.role in ['admin', 'editor']
    
    def can_delete(self):
        return self.role == 'admin'
    
    def can_manage_users(self):
        return self.role == 'admin'
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class FileLog(db.Model):
    __tablename__ = 'file_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    folder = db.Column(db.String(100), nullable=False)
    folder_path = db.Column(db.String(500))
    action = db.Column(db.String(20), nullable=False)  # upload, download, delete
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ip_address = db.Column(db.String(45))
    file_size = db.Column(db.Integer)  # en bytes
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.String(500))
    
    def __repr__(self):
        return f'<FileLog {self.action} {self.filename}>'

class SharedFolder(db.Model):
    __tablename__ = 'shared_folders'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    allowed_roles = db.Column(db.String(200), default='viewer,editor,admin')  # roles permitidos
    
    def __repr__(self):
        return f'<SharedFolder {self.name}>'
    
    def is_allowed_for_user(self, user):
        if not user or not user.is_authenticated:
            return False
        if user.role == 'admin':
            return True
        allowed = self.allowed_roles.split(',') if self.allowed_roles else []
        return user.role in allowed

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)