# app/routes.py
import os
import tempfile
from flask import Blueprint, render_template, send_file, request, redirect, url_for, flash, current_app, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import humanize

from .models import db, FileLog, SharedFolder
from .crypto_utils import FileEncryptor
from .decorators import permission_required, folder_access_required
from .forms import UploadForm

main_bp = Blueprint('main', __name__)

def allowed_file(filename):
    """Verifica si la extensión del archivo está permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def log_action(filename, folder, action, file_size=0, success=True, error=None):
    """Registra acciones de archivos para auditoría."""
    try:
        log = FileLog(
            filename=filename,
            original_filename=filename,
            folder=folder.name if hasattr(folder, 'name') else str(folder),
            folder_path=folder.path if hasattr(folder, 'path') else None,
            action=action,
            user_id=current_user.id,
            ip_address=request.remote_addr,
            file_size=file_size,
            success=success,
            error_message=str(error) if error else None
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging action: {e}")
        db.session.rollback()

def get_file_size_str(size_bytes):
    """Convierte bytes a formato legible."""
    return humanize.naturalsize(size_bytes)

@main_bp.route('/')
@login_required
def index():
    # Obtener carpetas compartidas de la BD o configuración
    folders = SharedFolder.query.filter_by(is_active=True).all()
    
    # Si no hay en BD, usar las de configuración
    if not folders:
        folders_list = []
        for name, path in current_app.config['SHARED_FOLDERS'].items():
            folder = {
                'id': None,
                'name': name,
                'path': path,
                'description': f'Carpeta compartida: {name}',
                'is_active': True
            }
            folders_list.append(folder)
        folders = folders_list
    
    return render_template('index.html', folders=folders)

@main_bp.route('/browse/<int:folder_id>')
@login_required
@folder_access_required
def browse(folder_id):
    folder = SharedFolder.query.get_or_404(folder_id)
    
    if not os.path.exists(folder.path):
        flash(f'La carpeta {folder.name} no existe en el sistema.', 'danger')
        return redirect(url_for('main.index'))
    
    # Obtener lista de archivos
    files = []
    try:
        for filename in os.listdir(folder.path):
            filepath = os.path.join(folder.path, filename)
            if os.path.isfile(filepath) and filename.endswith('.enc'):
                stats = os.stat(filepath)
                files.append({
                    'name': filename[:-4],  # Quitar .enc
                    'encrypted_name': filename,
                    'size': stats.st_size,
                    'size_str': get_file_size_str(stats.st_size),
                    'modified': datetime.fromtimestamp(stats.st_mtime),
                    'modified_str': humanize.naturaltime(datetime.fromtimestamp(stats.st_mtime)),
                    'path': filepath
                })
        
        # Ordenar por fecha modificada (más reciente primero)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
    except Exception as e:
        flash(f'Error al leer la carpeta: {e}', 'danger')
        return redirect(url_for('main.index'))
    
    form = UploadForm()
    form.folder_id.choices = [(folder.id, folder.name)]
    
    return render_template('browse.html', 
                         folder=folder, 
                         files=files,
                         form=form,
                         can_upload=current_user.can_upload(),
                         can_delete=current_user.can_delete())

@main_bp.route('/upload/<int:folder_id>', methods=['POST'])
@login_required
@permission_required('upload')
@folder_access_required
def upload(folder_id):
    folder = SharedFolder.query.get_or_404(folder_id)
    
    if 'files[]' not in request.files:
        flash('No se seleccionó ningún archivo.', 'danger')
        return redirect(url_for('main.browse', folder_id=folder_id))
    
    files = request.files.getlist('files[]')
    
    if not files or files[0].filename == '':
        flash('No se seleccionaron archivos.', 'danger')
        return redirect(url_for('main.browse', folder_id=folder_id))
    
    encryptor = FileEncryptor()
    uploaded = 0
    errors = []
    
    for file in files:
        if not allowed_file(file.filename):
            errors.append(f'{file.filename}: Tipo de archivo no permitido')
            continue
        
        filename = secure_filename(file.filename)
        
        # Verificar si ya existe
        encrypted_path = os.path.join(folder.path, filename + '.enc')
        if os.path.exists(encrypted_path):
            # Añadir timestamp al nombre
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}{ext}"
        
        try:
            # Cifrar directamente desde el objeto file
            encrypted_path = os.path.join(folder.path, filename + '.enc')
            encryptor.encrypt_file_object(file.stream, encrypted_path)
            
            # Registrar en log
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            log_action(filename, folder, 'upload', file_size)
            
            uploaded += 1
            
        except Exception as e:
            errors.append(f'{filename}: Error al cifrar - {str(e)}')
            log_action(filename, folder, 'upload', success=False, error=e)
    
    if uploaded > 0:
        flash(f'{uploaded} archivo(s) subido(s) correctamente.', 'success')
    for error in errors:
        flash(error, 'danger')
    
    return redirect(url_for('main.browse', folder_id=folder_id))

@main_bp.route('/download/<int:folder_id>/<path:filename>')
@login_required
@folder_access_required
def download(folder_id, filename):
    folder = SharedFolder.query.get_or_404(folder_id)
    
    # Validaciones de seguridad
    if '..' in filename or filename.startswith('/') or '\\' in filename:
        abort(400, description="Nombre de archivo inválido")
    
    encrypted_path = os.path.join(folder.path, filename)
    if not os.path.exists(encrypted_path) or not os.path.isfile(encrypted_path):
        abort(404, description="Archivo no encontrado")
    
    if not filename.endswith('.enc'):
        abort(400, description="Tipo de archivo no soportado")
    
    # Crear archivo temporal para el contenido descifrado
    temp_fd, temp_decrypted = tempfile.mkstemp(suffix='_' + filename[:-4])
    os.close(temp_fd)
    
    try:
        # Descifrar
        encryptor = FileEncryptor()
        encryptor.decrypt_file(encrypted_path, temp_decrypted)
        
        # Obtener nombre original (quitar .enc)
        original_name = filename[:-4]
        
        # Obtener tamaño para el log
        file_size = os.path.getsize(encrypted_path)
        
        # Registrar descarga
        log_action(original_name, folder, 'download', file_size)
        
        # Enviar archivo
        return send_file(
            temp_decrypted,
            as_attachment=True,
            download_name=original_name,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        # Limpiar en caso de error
        if os.path.exists(temp_decrypted):
            os.unlink(temp_decrypted)
        log_action(filename, folder, 'download', success=False, error=e)
        flash(f'Error al descargar el archivo: {str(e)}', 'danger')
        return redirect(url_for('main.browse', folder_id=folder_id))

@main_bp.route('/delete/<int:folder_id>/<path:filename>')
@login_required
@permission_required('delete')
@folder_access_required
def delete(folder_id, filename):
    folder = SharedFolder.query.get_or_404(folder_id)
    
    # Validaciones de seguridad
    if '..' in filename or filename.startswith('/') or '\\' in filename:
        abort(400, description="Nombre de archivo inválido")
    
    encrypted_path = os.path.join(folder.path, filename)
    if not os.path.exists(encrypted_path) or not os.path.isfile(encrypted_path):
        abort(404, description="Archivo no encontrado")
    
    try:
        # Obtener información para el log
        original_name = filename[:-4] if filename.endswith('.enc') else filename
        file_size = os.path.getsize(encrypted_path)
        
        # Eliminar archivo
        os.remove(encrypted_path)
        
        # Registrar eliminación
        log_action(original_name, folder, 'delete', file_size)
        
        flash(f'Archivo {original_name} eliminado correctamente.', 'success')
        
    except Exception as e:
        log_action(filename, folder, 'delete', success=False, error=e)
        flash(f'Error al eliminar: {str(e)}', 'danger')
    
    return redirect(url_for('main.browse', folder_id=folder_id))

@main_bp.route('/search')
@login_required
def search():
    """Búsqueda de archivos."""
    query = request.args.get('q', '')
    if len(query) < 3:
        flash('La búsqueda debe tener al menos 3 caracteres.', 'warning')
        return redirect(url_for('main.index'))
    
    results = []
    folders = SharedFolder.query.filter_by(is_active=True).all()
    
    for folder in folders:
        if not folder.is_allowed_for_user(current_user):
            continue
            
        if os.path.exists(folder.path):
            for filename in os.listdir(folder.path):
                if filename.endswith('.enc') and query.lower() in filename.lower():
                    stats = os.stat(os.path.join(folder.path, filename))
                    results.append({
                        'name': filename[:-4],
                        'encrypted_name': filename,
                        'folder': folder.name,
                        'folder_id': folder.id,
                        'size_str': get_file_size_str(stats.st_size),
                        'modified_str': humanize.naturaltime(datetime.fromtimestamp(stats.st_mtime))
                    })
    
    return render_template('search.html', results=results, query=query)

@main_bp.route('/api/folders')
@login_required
def api_folders():
    """API para obtener carpetas (formato JSON)."""
    folders = SharedFolder.query.filter_by(is_active=True).all()
    result = []
    for folder in folders:
        if folder.is_allowed_for_user(current_user):
            result.append({
                'id': folder.id,
                'name': folder.name,
                'description': folder.description
            })
    return jsonify(result)

@main_bp.route('/api/files/<int:folder_id>')
@login_required
@folder_access_required
def api_files(folder_id):
    """API para obtener archivos de una carpeta."""
    folder = SharedFolder.query.get_or_404(folder_id)
    
    files = []
    if os.path.exists(folder.path):
        for filename in os.listdir(folder.path):
            if filename.endswith('.enc'):
                stats = os.stat(os.path.join(folder.path, filename))
                files.append({
                    'name': filename[:-4],
                    'encrypted_name': filename,
                    'size': stats.st_size,
                    'size_str': get_file_size_str(stats.st_size),
                    'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    'modified_str': humanize.naturaltime(datetime.fromtimestamp(stats.st_mtime))
                })
    
    return jsonify(files)