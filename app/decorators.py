# app/decorators.py
from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, inicia sesión para acceder.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin:
            flash('Acceso denegado. Se requieren privilegios de administrador.', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def editor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, inicia sesión para acceder.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.can_upload():
            flash('Acceso denegado. Se requieren permisos de editor.', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

def permission_required(action):
    """Decorador genérico para permisos."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor, inicia sesión para acceder.', 'warning')
                return redirect(url_for('auth.login'))
            
            if action == 'upload' and not current_user.can_upload():
                flash('No tienes permiso para subir archivos.', 'danger')
                return redirect(url_for('main.index'))
            
            if action == 'delete' and not current_user.can_delete():
                flash('No tienes permiso para eliminar archivos.', 'danger')
                return redirect(url_for('main.index'))
            
            if action == 'manage_users' and not current_user.can_manage_users():
                flash('No tienes permiso para gestionar usuarios.', 'danger')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def folder_access_required(f):
    """Verifica que el usuario tenga acceso a la carpeta."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from .models import SharedFolder
        
        folder_id = kwargs.get('folder_id')
        if folder_id:
            folder = SharedFolder.query.get_or_404(folder_id)
            if not folder.is_allowed_for_user(current_user):
                flash('No tienes acceso a esta carpeta.', 'danger')
                return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function