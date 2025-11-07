"""Script de depuración para verificar y arreglar la base de datos"""
import os
from app_empenos_web import app, db, Admin, User, Empeno

def verificar_db():
    with app.app_context():
        print("=== Verificando Base de Datos ===\n")
        
        # Verificar tablas
        print("Tablas en la base de datos:")
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"  {tables}\n")
        
        # Verificar admin
        print("Verificando tabla Admin:")
        try:
            admin_count = Admin.query.count()
            print(f"  Admins en DB: {admin_count}")
            
            admins = Admin.query.all()
            for a in admins:
                print(f"    - {a.username}")
        except Exception as e:
            print(f"  ERROR: {e}")
        
        # Verificar usuarios
        print("\nVerificando tabla User:")
        try:
            user_count = User.query.count()
            print(f"  Usuarios en DB: {user_count}")
            
            users = User.query.all()
            for u in users:
                print(f"    - {u.nombre} (DNI: {u.dni})")
        except Exception as e:
            print(f"  ERROR: {e}")
        
        # Verificar empeños
        print("\nVerificando tabla Empeno:")
        try:
            empeno_count = Empeno.query.count()
            print(f"  Empeños en DB: {empeno_count}")
        except Exception as e:
            print(f"  ERROR: {e}")

def recrear_db():
    """Recrear todas las tablas"""
    with app.app_context():
        print("\n=== Recreando Base de Datos ===\n")
        
        # Eliminar todas las tablas
        print("Eliminando tablas existentes...")
        db.drop_all()
        
        # Crear todas las tablas
        print("Creando tablas nuevas...")
        db.create_all()
        
        # Crear admin por defecto
        print("Creando admin por defecto (admin/admin)...")
        admin = Admin(username='admin')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        
        print("✓ Base de datos recreada exitosamente!\n")
        verificar_db()

if __name__ == '__main__':
    print("Script de Depuración - Sistema de Empeños")
    print("=" * 50)
    
    verificar_db()
    
    respuesta = input("\n¿Desea recrear la base de datos? (s/N): ")
    if respuesta.lower() == 's':
        recrear_db()
        print("\n✓ Proceso completado!")
    else:
        print("\nNo se realizaron cambios.")
