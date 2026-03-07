# app/admin.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import os
from .models import db, User, FileLog, SharedFolder, SystemSetting
from .forms import UserEditForm, FolderForm
from .decorators import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Estadísticas rápidas
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_files = FileLog.query.filter_by(action='upload').count()
    total_downloads = FileLog.query.filter_by(action='download').count()
    
    # Actividad reciente (últimos 7 días)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_activity = FileLog.query.filter(FileLog.timestamp >= week_ago).count()
    
    # Usuarios nuevos este mes
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_month = User.query.filter(User.created_at >= month_start).count()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_files=total_files,
                         total_downloads=total_downloads,
                         recent_activity=recent_activity,
                         new_users_month=new_users_month)

@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Estadísticas del usuario
    total_uploads = FileLog.query.filter_by(user_id=user_id, action='upload').count()
    total_downloads = FileLog.query.filter_by(user_id=user_id, action='download').count()
    total_deleted = FileLog.query.filter_by(user_id=user_id, action='delete').count()
    
    # Últimas actividades
    recent_logs = FileLog.query.filter_by(user_id=user_id)\
                               .order_by(desc(FileLog.timestamp))\
                               .limit(20).all()
    
    return render_template('admin/view_user.html',
                         user=user,
                         total_uploads=total_uploads,
                         total_downloads=total_downloads,
                         total_deleted=total_deleted,
                         recent_logs=recent_logs)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id and user.role != 'admin':
        flash('No puedes cambiar tu propio rol de administrador.', 'warning')
    
    form = UserEditForm(obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        
        if form.new_password.data:
            user.set_password(form.new_password.data)
        
        db.session.commit()
        flash(f'Usuario {user.username} actualizado correctamente.', 'success')
        return redirect(url_for('admin.view_user', user_id=user.id))
    
    return render_template('admin/edit_user.html', form=form, user=user)

@admin_bp.route('/users/<int:user_id>/delete')
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('No puedes eliminarte a ti mismo.', 'danger')
        return redirect(url_for('admin.list_users'))
    
    user = User.query.get_or_404(user_id)
    
    # Verificar si tiene archivos asociados
    file_count = FileLog.query.filter_by(user_id=user_id).count()
    
    if file_count > 0 and not request.args.get('confirm'):
        flash(f'El usuario tiene {file_count} archivos asociados. ¿Estás seguro?', 'warning')
        return redirect(url_for('admin.view_user', user_id=user_id, confirm=1))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Usuario {username} eliminado.', 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/logs')
@login_required
@admin_required
def view_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    action = request.args.get('action', '')
    user_id = request.args.get('user_id', type=int)
    
    query = FileLog.query
    
    if action:
        query = query.filter_by(action=action)
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    logs = query.order_by(desc(FileLog.timestamp)).paginate(page=page, per_page=per_page)
    
    return render_template('admin/logs.html', logs=logs, action=action, user_id=user_id)

@admin_bp.route('/folders')
@login_required
@admin_required
def list_folders():
    folders = SharedFolder.query.all()
    return render_template('admin/folders.html', folders=folders)

@admin_bp.route('/folders/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_folder():
    form = FolderForm()
    
    if form.validate_on_submit():
        # Verificar que la ruta existe o crearla
        path = os.path.abspath(form.path.data)
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            flash(f'Error al crear la carpeta: {e}', 'danger')
            return render_template('admin/add_folder.html', form=form)
        
        folder = SharedFolder(
            name=form.name.data,
            path=path,
            description=form.description.data,
            allowed_roles=form.allowed_roles.data,
            is_active=form.is_active.data,
            created_by=current_user.id
        )
        
        db.session.add(folder)
        db.session.commit()
        
        flash(f'Carpeta {folder.name} añadida correctamente.', 'success')
        return redirect(url_for('admin.list_folders'))
    
    return render_template('admin/add_folder.html', form=form)

@admin_bp.route('/folders/<int:folder_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_folder(folder_id):
    folder = SharedFolder.query.get_or_404(folder_id)
    form = FolderForm(obj=folder)
    
    if form.validate_on_submit():
        folder.name = form.name.data
        folder.description = form.description.data
        folder.allowed_roles = form.allowed_roles.data
        folder.is_active = form.is_active.data
        
        db.session.commit()
        flash(f'Carpeta {folder.name} actualizada.', 'success')
        return redirect(url_for('admin.list_folders'))
    
    return render_template('admin/edit_folder.html', form=form, folder=folder)

@admin_bp.route('/folders/<int:folder_id>/delete')
@login_required
@admin_required
def delete_folder(folder_id):
    folder = SharedFolder.query.get_or_404(folder_id)
    
    # Verificar si tiene archivos
    if os.path.exists(folder.path) and os.listdir(folder.path):
        flash('La carpeta no está vacía. Elimina los archivos primero.', 'danger')
        return redirect(url_for('admin.list_folders'))
    
    db.session.delete(folder)
    db.session.commit()
    
    flash(f'Carpeta {folder.name} eliminada.', 'success')
    return redirect(url_for('admin.list_folders'))

@admin_bp.route('/stats')
@login_required
@admin_required
def stats():
    # Estadísticas generales
    total_users = User.query.count()
    total_files = FileLog.query.filter_by(action='upload').count()
    total_downloads = FileLog.query.filter_by(action='download').count()
    total_delete = FileLog.query.filter_by(action='delete').count()
    
    # Almacenamiento total
    total_storage = db.session.query(func.sum(FileLog.file_size))\
                              .filter(FileLog.action == 'upload')\
                              .scalar() or 0
    
    # Usuarios más activos
    active_users = db.session.query(
        User.username,
        func.count(FileLog.id).label('total_actions')
    ).join(FileLog).group_by(User.id).order_by(desc('total_actions')).limit(10).all()
    
    # Actividad por día (últimos 30 días)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_activity = db.session.query(
        func.date(FileLog.timestamp).label('date'),
        func.count().label('count')
    ).filter(FileLog.timestamp >= thirty_days_ago)\
     .group_by(func.date(FileLog.timestamp))\
     .order_by('date').all()
    
    return render_template('admin/stats.html',
                         total_users=total_users,
                         total_files=total_files,
                         total_downloads=total_downloads,
                         total_delete=total_delete,
                         total_storage=total_storage,
                         active_users=active_users,
                         daily_activity=daily_activity)