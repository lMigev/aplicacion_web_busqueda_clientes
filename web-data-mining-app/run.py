#!/usr/bin/env python3
"""
Punto de entrada principal para la aplicación web de minería de datos.
Ejecutar con: python run.py
"""
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    try:
        from app import app
        print("🚀 Iniciando aplicación web de minería de datos...")
        print("📍 Accede a: http://127.0.0.1:5000")
        print("🔧 Modo debug activado")
        print("⏹️  Presiona Ctrl+C para detener")
        
        app.run(host='127.0.0.1', port=5000, debug=True)
        
    except KeyboardInterrupt:
        print("\n👋 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"❌ Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
