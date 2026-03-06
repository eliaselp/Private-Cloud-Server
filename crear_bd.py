#!/usr/bin/env python
# fix_db_completo.py
import os
import sqlite3
from app import create_app, db
from app.models import User
from sqlalchemy import inspect
from sqlalchemy import text
def crear_base_datos():
    """Función principal que crea y configura la base de datos"""
    
    print("=" * 60)
    print("🔧 REPARACIÓN COMPLETA DE BASE DE DATOS")
    print("=" * 60)
    
    # PASO 1: Crear BD con sqlite3 puro
    print("\n📁 PASO 1: Creando archivo de base de datos...")
    db_path = os.path.abspath('instance/nube.db')
    print(f"   Ruta: {db_path}")
    
    # Asegurar que el directorio instance existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Crear/conectar a la BD
    conn = sqlite3.connect(db_path)
    conn.close()
    print(f"   ✅ Archivo BD creado/verificado")
    
    # Verificar que existe
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        permisos = oct(os.stat(db_path).st_mode)[-3:]
        print(f"   📁 Tamaño: {size} bytes")
        print(f"   📁 Permisos: {permisos}")
    
    # PASO 2: Crear tablas con SQLAlchemy
    print("\n🔄 PASO 2: Creando tablas con SQLAlchemy...")
    app = create_app()
    
    with app.app_context():
        # Forzar recreación del engine
        db.engine.dispose()
        print("   ✅ Engine de SQLAlchemy reiniciado")
        
        # Crear todas las tablas
        db.create_all()
        print("   ✅ Tablas creadas con SQLAlchemy")
        
        # Verificar tablas creadas
        inspector = inspect(db.engine)
        tablas = inspector.get_table_names()
        print(f"   📊 Tablas encontradas: {tablas}")
        
        # PASO 3: Crear usuario admin
        print("\n👤 PASO 3: Verificando usuario admin...")
        if not User.query.first():
            admin = User(
                username='admin',
                email='admin@localhost.com',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("   ✅ Usuario admin creado")
            print("      Usuario: admin")
            print("      Contraseña: admin123")
        else:
            print("   ✅ Usuario admin ya existe")
        
        # Mostrar todos los usuarios
        usuarios = User.query.all()
        print(f"\n👥 Usuarios en sistema: {len(usuarios)}")
        for user in usuarios:
            print(f"   - {user.username} ({user.role})")
        
        # PASO 4: Verificación final
        print("\n✅ PASO 4: Verificación final")
        
        # Probar consulta
        try:
            result = db.session.execute(text("SELECT 1")).scalar()
            print(f"   ✅ Conexión a BD verificada: {result}")
        except Exception as e:
            print(f"   ❌ Error en conexión: {e}")
        
        # Verificar integridad
        
        try:
            # Contar registros en cada tabla
            for tabla in tablas:
                count = db.session.execute(text(f"SELECT COUNT(*) FROM {tabla}")).scalar()
                print(f"   📊 {tabla}: {count} registros")
        except Exception as e:
            print(f"   ❌ Error al contar registros: {e}")
    
    print("\n" + "=" * 60)
    print("✅ REPARACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print("\nAhora puedes ejecutar: python run.py")
    print("Y acceder a: http://localhost:5000")
    print("Usuario: admin")
    print("Contraseña: admin123")

if __name__ == "__main__":
    crear_base_datos()