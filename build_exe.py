import subprocess
import sys
import os

def install_pyinstaller():
    print("Verificando/Instalando PyInstaller en el entorno virtual...")
    # Usar el pip del entorno virtual
    pip_path = os.path.join(".venv", "Scripts", "pip.exe")
    if not os.path.exists(pip_path):
        pip_path = "pip" # fallback
    subprocess.run([pip_path, "install", "pyinstaller"], check=True)

def build():
    print("Compilando el proyecto con PyInstaller...")
    pyinstaller_path = os.path.join(".venv", "Scripts", "pyinstaller.exe")
    if not os.path.exists(pyinstaller_path):
        pyinstaller_path = "pyinstaller"
        
    # Comando de PyInstaller
    cmd = [
        pyinstaller_path,
        "--name=FootballPredictor",
        "--onefile",
        "--noconsole",
        "--icon=app_icon.ico",
        "--hidden-import=groq",
        "--hidden-import=mistralai",
        "--add-data=templates;templates",
        "--add-data=static;static",
        "--add-data=TABLAS DE POSICIONES.xlsx;.",
        "launcher.py"
    ]
    
    print(f"Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print("\n¡Compilación completada! El archivo ejecutable se encuentra en la carpeta 'dist/'.")

if __name__ == "__main__":
    install_pyinstaller()
    build()
