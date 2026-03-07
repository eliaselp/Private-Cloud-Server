# Mi Nube Privada - Almacenamiento Seguro con Cifrado AES-256

## 📋 Descripción General

**Mi Nube Privada** es una solución de almacenamiento en la nube auto-alojada desarrollada en Python, diseñada para proporcionar un espacio seguro y privado para tus archivos. A diferencia de servicios comerciales como Dropbox o Google Drive, este proyecto te da control total sobre tus datos, que se almacenan en tus propios servidores con cifrado de extremo a extremo.

## ✨ Características Principales

### 🔐 Seguridad
- **Cifrado AES-256 en reposo**: Todos los archivos se cifran antes de guardarse en el disco utilizando la biblioteca `cryptography`.
- **Autenticación robusta**: Sistema de login con contraseñas hasheadas (pbkdf2:sha256).
- **Protección CSRF**: Implementada en todos los formularios.
- **Sesiones seguras**: Cookies HTTP-only y configuración de seguridad avanzada.

### 👥 Gestión de Usuarios
- **Tres roles de usuario**:
  - **Administrador**: Control total (subir, descargar, eliminar, gestionar usuarios)
  - **Editor**: Puede subir y descargar archivos
  - **Espectador**: Solo puede ver y descargar archivos
- **Gestión completa de usuarios**: Crear, editar, activar/desactivar y eliminar usuarios.
- **Perfiles de usuario**: Cada usuario puede cambiar su email y contraseña.

### 📁 Gestión de Archivos
- **Múltiples carpetas compartidas**: Configurables desde variables de entorno.
- **Subida de archivos**: Soporte para múltiples archivos simultáneamente.
- **Descarga segura**: Los archivos se descifran sobre la marcha antes de la descarga.
- **Eliminación de archivos**: Solo para administradores.
- **Búsqueda de archivos**: Búsqueda por nombre en todas las carpetas.

### 📊 Administración y Monitoreo
- **Panel de administración**: Dashboard con estadísticas del sistema.
- **Registro de actividad (logs)**: Auditoría completa de todas las acciones (subidas, descargas, eliminaciones).
- **Estadísticas visuales**: Gráficos de actividad con Chart.js.
- **Gestión de carpetas compartidas**: Añadir, editar y desactivar carpetas desde la interfaz web.

### 🗄️ Base de Datos
- **SQLite** con SQLAlchemy como ORM.
- **Migraciones con Alembic** para control de versiones de la BD.
- **Modelos**: Usuarios, logs de actividad, carpetas compartidas y configuración del sistema.

## 🛠️ Tecnologías Utilizadas

| Tecnología | Propósito |
|------------|-----------|
| **Python 3.10+** | Lenguaje base |
| **Flask 2.3** | Framework web |
| **Flask-SQLAlchemy** | ORM para base de datos |
| **Flask-Login** | Gestión de sesiones de usuario |
| **Flask-Migrate** | Migraciones de base de datos |
| **Flask-WTF / WTForms** | Formularios y validación |
| **Cryptography** | Cifrado AES-256 de archivos |
| **SQLite** | Base de datos (fácil de移植ar) |
| **Bootstrap 5** | Interfaz de usuario responsive |
| **Chart.js** | Gráficos estadísticos |
| **Humanize** | Formato legible de tamaños y fechas |

## 📁 Estructura del Proyecto

```
mi_nube_privada/
├── app/
│   ├── __init__.py          # Inicialización de Flask y extensiones
│   ├── models.py             # Modelos de base de datos
│   ├── forms.py              # Formularios WTForms
│   ├── auth.py               # Autenticación (login/logout/registro)
│   ├── admin.py              # Rutas de administración
│   ├── routes.py             # Rutas principales (archivos, carpetas)
│   ├── crypto_utils.py       # Utilidades de cifrado AES-256
│   ├── decorators.py         # Decoradores personalizados (permisos)
│   ├── templates/            # Plantillas HTML
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── browse.html
│   │   ├── login.html
│   │   ├── admin/
│   │   │   ├── dashboard.html
│   │   │   ├── users.html
│   │   │   └── ...
│   │   └── includes/
│   │       └── navbar.html
│   └── static/               # CSS, JS, imágenes
├── instance/
│   ├── nube.db               # Base de datos SQLite
│   └── logs/                  # Logs de la aplicación
├── migrations/                # Migraciones de base de datos
├── shared_docs/               # Carpeta compartida por defecto
├── shared_images/             # Carpeta compartida por defecto
├── config.py                  # Configuración de la aplicación
├── run.py                     # Punto de entrada
├── requirements.txt           # Dependencias
└── .env                       # Variables de entorno (claves secretas)
```

## 🚀 Instalación y Configuración

### Requisitos Previos
- Python 3.10 o superior
- pip (gestor de paquetes)
- Entorno virtual (recomendado)

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/eliaselp/Private-Cloud-Server.git
   cd Private-Cloud-Server
   ```

2. **Crear y activar entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # o
   venv\Scripts\activate     # Windows
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno (archivo `.env`)**
   ```env
   SECRET_KEY=tu-clave-secreta-muy-larga-cambia-esto
   WTF_CSRF_SECRET_KEY=otra-clave-diferente-para-csrf
   ENCRYPTION_KEY=clave-para-cifrado-aes-256-generada-con-fernett
   SHARED_FOLDERS=Documentos:./shared_docs,Imagenes:./shared_images
   FLASK_DEBUG=True
   ```

5. **Inicializar la base de datos**
   ```bash
   python crear_bd.py
   ```

6. **Ejecutar la aplicación**
   ```bash
   python run.py
   ```

7. **Acceder a la aplicación**
   - URL: http://localhost:5000
   - Usuario por defecto: **admin**
   - Contraseña por defecto: **admin123**

## 🔧 Configuración Avanzada

### Carpetas Compartidas
Las carpetas se configuran en `.env` con el formato:
```
SHARED_FOLDERS=Nombre1:./ruta1,Nombre2:./ruta2
```

### Clave de Cifrado
Para generar una clave de cifrado válida:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 👥 Roles y Permisos

| Acción | Admin | Editor | Espectador |
|--------|-------|--------|------------|
| Ver archivos | ✅ | ✅ | ✅ |
| Descargar | ✅ | ✅ | ✅ |
| Subir archivos | ✅ | ✅ | ❌ |
| Eliminar archivos | ✅ | ❌ | ❌ |
| Gestionar usuarios | ✅ | ❌ | ❌ |
| Ver logs | ✅ | ❌ | ❌ |
| Gestionar carpetas | ✅ | ❌ | ❌ |

## 📊 Interfaz de Usuario

### Página Principal
- Lista de carpetas compartidas disponibles
- Acceso rápido a cada carpeta

### Explorador de Archivos
- Lista de archivos con nombre, tamaño y fecha
- Botones de descarga (todos los roles)
- Botones de subida (admin/editor)
- Botones de eliminación (solo admin)

### Panel de Administración
- Dashboard con estadísticas
- Gestión de usuarios (CRUD completo)
- Gestión de carpetas compartidas
- Logs de actividad con filtros
- Gráficos estadísticos

## 🔒 Seguridad Implementada

1. **Cifrado de archivos**: AES-256 con Fernet (biblioteca cryptography)
2. **Contraseñas hasheadas**: pbkdf2:sha256 con salt
3. **Protección CSRF**: En todos los formularios
4. **Sesiones seguras**: Cookies HTTP-only
5. **Validación de archivos**: Extensiones permitidas y tamaño máximo
6. **Auditoría**: Registro de todas las acciones de archivos
7. **Separación de roles**: Permisos granulares por tipo de usuario

## 📝 Licencia

Este proyecto está bajo la Licencia MIT.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request


**¡Disfruta de tu nube privada, segura y bajo tu control!** 🚀
