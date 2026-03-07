# config.py
import os
from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY')
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY')
    
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application")
    if not WTF_CSRF_SECRET_KEY:
        raise ValueError("No WTF_CSRF_SECRET_KEY set for Flask application")
    
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'nube.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cifrado
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    if not ENCRYPTION_KEY:
        raise ValueError("No ENCRYPTION_KEY set for Flask application")
    
    # Carpetas compartidas desde .env
    SHARED_FOLDERS = {}
    folders_str = os.environ.get('SHARED_FOLDERS', '')
    if folders_str:
        for folder_config in folders_str.split(','):
            try:
                name, path = folder_config.split(':')
                abs_path = os.path.abspath(path.strip())
                os.makedirs(abs_path, exist_ok=True)
                SHARED_FOLDERS[name.strip()] = abs_path
            except ValueError:
                print(f"Warning: Invalid folder config: {folder_config}")
    
    # Extensiones permitidas
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
                          'xls', 'xlsx', 'mp4', 'avi', 'mp3', 'zip', 'rar', '7z','py','exe','gz',
                          'xml', 'yaml','html','css','js','jsx'}
    
    # Tamaño máximo de archivo (20GB)
    MAX_CONTENT_LENGTH = 20000 * 1024 * 1024
    
    # Configuración de sesión
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Cambiar a True en producción con HTTPS
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600 * 24 * 30  # 30 días