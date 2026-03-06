# app/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from .models import db, User
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, ProfileForm
from .decorators import admin_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Esta cuenta está desactivada. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))
            
            # Actualizar último login e IP
            user.last_login = datetime.utcnow()
            user.last_ip = request.remote_addr
            db.session.commit()
            
            login_user(user, remember=form.remember.data)
            
            next_page = request.args.get('next')
            flash(f'¡Bienvenido, {user.username}!', 'success')
            
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Usuario {user.username} creado correctamente.', 'success')
        return redirect(url_for('admin.list_users'))
    
    return render_template('register.html', form=form)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.email = form.email.data
        db.session.commit()
        flash('Perfil actualizado correctamente.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('profile.html', form=form, user=current_user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Contraseña cambiada correctamente.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Contraseña actual incorrecta.', 'danger')
    
    return render_template('change_password.html', form=form)