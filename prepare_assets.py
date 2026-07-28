import subprocess
import sys
import os

def install_pillow():
    print("Verificando/Instalando Pillow...")
    pip_path = os.path.join(".venv", "Scripts", "pip.exe")
    if not os.path.exists(pip_path):
        pip_path = "pip"
    subprocess.run([pip_path, "install", "pillow"], check=True)

def convert_images():
    from PIL import Image
    
    source_img_path = r"C:\Users\JEFE ENFERMERIA\.gemini\antigravity-ide\brain\16585026-b7fd-4373-bd56-784eec19ac2e\media__1782849315178.jpg"
    if not os.path.exists(source_img_path):
        print(f"Error: No se encontró la imagen origen en {source_img_path}")
        return
        
    print("Abriendo imagen origen...")
    img = Image.open(source_img_path)
    
    # 1. Guardar como Icono (.ico)
    print("Generando app_icon.ico...")
    img.save("app_icon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    
    # 2. Redimensionar para el Banner GUI (ancho 400, alto 225)
    print("Generando templates/banner.png...")
    banner_img = img.resize((400, 225), Image.Resampling.LANCZOS)
    os.makedirs("templates", exist_ok=True)
    banner_img.save(os.path.join("templates", "banner.png"), format="PNG")
    print("Recursos listos.")

if __name__ == "__main__":
    install_pillow()
    convert_images()
