import sys
import os
import traceback

def log_crash(err_msg):
    exec_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(".")
    log_path = os.path.join(exec_dir, "crash_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(err_msg)

try:
    import threading
    import webbrowser
    import tkinter as tk
    from werkzeug.serving import make_server
    from PIL import Image, ImageTk  # Cargar Pillow para imágenes
    from app import app  # Importar la app de Flask
except Exception as e:
    log_crash(traceback.format_exc())
    sys.exit(1)

class FlaskServerThread(threading.Thread):
    def __init__(self, app):
        super().__init__()
        self.server = make_server('127.0.0.1', 5001, app, threaded=True)
        self.daemon = True

    def run(self):
        print("Iniciando servidor Flask...")
        self.server.serve_forever()

    def shutdown(self):
        print("Deteniendo servidor Flask...")
        self.server.shutdown()

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FutboltAI - Panel de Control")
        
        # Centrar la ventana y establecer tamaño
        self.width = 400
        self.height = 420
        self.center_window(self.width, self.height)
        
        self.server_thread = None
        self.is_running = False

        # Configuración de ventana sin bordes (borderless)
        self.root.overrideredirect(True)
        self.root.configure(bg="#00e87a") # Borde neón externo

        # Diseñar Interfaz
        self.create_widgets()
        
        # Iniciar servidor por defecto
        self.toggle_server()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def drag_window(self, event):
        deltax = event.x - self.drag_x
        deltay = event.y - self.drag_y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def create_widgets(self):
        # Contenedor principal con fondo oscuro
        main_container = tk.Frame(self.root, bg="#060711", bd=0)
        main_container.pack(fill="both", expand=True, padx=1, pady=1) # Deja ver 1px de borde neón

        # 1. BARRA DE TÍTULO PERSONALIZADA
        title_bar = tk.Frame(main_container, bg="#060711", height=32)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)

        # Arrastre en la barra superior
        title_bar.bind("<Button-1>", self.start_drag)
        title_bar.bind("<B1-Motion>", self.drag_window)

        # Logotipo y título
        title_lbl = tk.Label(
            title_bar, text="⚽ FutboltAI", 
            font=('Segoe UI', 10, 'bold'), fg="#00e87a", bg="#060711"
        )
        title_lbl.pack(side="left", padx=10)
        title_lbl.bind("<Button-1>", self.start_drag)
        title_lbl.bind("<B1-Motion>", self.drag_window)

        # Botón de cierre
        close_btn = tk.Button(
            title_bar, text="✕", bg="#060711", fg="#8892a4",
            activebackground="#ef4444", activeforeground="#ffffff",
            bd=0, font=("Segoe UI", 10, "bold"), width=4, height=1,
            cursor="hand2", command=self.on_closing
        )
        close_btn.pack(side="right", fill="y")
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg="#ef4444", fg="#ffffff"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg="#060711", fg="#8892a4"))

        # 2. BANNER DE MARCA
        if getattr(sys, 'frozen', False):
            banner_path = os.path.join(sys._MEIPASS, 'templates', 'banner.png')
        else:
            banner_path = os.path.join('templates', 'banner.png')

        if os.path.exists(banner_path):
            try:
                self.pil_img = Image.open(banner_path)
                self.banner_img = ImageTk.PhotoImage(self.pil_img)
                banner_label = tk.Label(main_container, image=self.banner_img, bg="#060711", bd=0)
                banner_label.pack(pady=0)
            except Exception as e:
                print(f"Error cargando imagen: {e}")
                fallback_title = tk.Label(
                    main_container, text="⚽ FutboltAI", 
                    font=('Segoe UI', 20, 'bold'), fg="#00e87a", bg="#060711"
                )
                fallback_title.pack(pady=30)
        else:
            fallback_title = tk.Label(
                main_container, text="⚽ FutboltAI", 
                font=('Segoe UI', 20, 'bold'), fg="#00e87a", bg="#060711"
            )
            fallback_title.pack(pady=30)

        # 3. INDICADOR DE ESTADO
        self.status_label = tk.Label(
            main_container, text="Estado: Apagado", 
            font=('Segoe UI', 11, 'bold'), fg="#ef4444", bg="#060711"
        )
        self.status_label.pack(pady=15)

        # 4. CONTENEDOR DE BOTONES
        btn_frame = tk.Frame(main_container, bg="#060711")
        btn_frame.pack(pady=10)

        # Botón Iniciar/Detener (Estilo Premium)
        self.action_btn = tk.Button(
            btn_frame, text="Iniciar Servidor", command=self.toggle_server,
            bg="#110f18", fg="#00e87a", activebackground="#00e87a", activeforeground="#002e1a",
            bd=1, relief="solid", highlightthickness=0, font=('Segoe UI', 10, 'bold'),
            width=16, height=2, cursor="hand2"
        )
        self.action_btn.grid(row=0, column=0, padx=10)

        # Botón Abrir Navegador (Estilo Premium)
        self.browser_btn = tk.Button(
            btn_frame, text="Abrir Navegador", command=self.open_browser,
            bg="#0a0a0f", fg="#555555", activebackground="#7c3aed", activeforeground="#ffffff",
            bd=1, relief="solid", highlightthickness=0, font=('Segoe UI', 10, 'bold'),
            width=16, height=2, cursor="hand2", state="disabled"
        )
        self.browser_btn.grid(row=0, column=1, padx=10)

        # Sincronizar estilos reactivos
        self.update_button_styles()

    def update_button_styles(self):
        if self.is_running:
            # Botón de detener (Rojo)
            self.action_btn.config(text="Detener Servidor", fg="#ef4444")
            self.action_btn.bind("<Enter>", lambda e: self.action_btn.config(bg="#ef4444", fg="#ffffff"))
            self.action_btn.bind("<Leave>", lambda e: self.action_btn.config(bg="#110f18", fg="#ef4444"))
            
            # Botón del navegador (Azul/Celeste)
            self.browser_btn.config(state="normal", fg="#3b82f6", bg="#110f18")
            self.browser_btn.bind("<Enter>", lambda e: self.browser_btn.config(bg="#3b82f6", fg="#ffffff"))
            self.browser_btn.bind("<Leave>", lambda e: self.browser_btn.config(bg="#110f18", fg="#3b82f6"))
        else:
            # Botón de iniciar (Verde)
            self.action_btn.config(text="Iniciar Servidor", fg="#00e87a")
            self.action_btn.bind("<Enter>", lambda e: self.action_btn.config(bg="#00e87a", fg="#002e1a"))
            self.action_btn.bind("<Leave>", lambda e: self.action_btn.config(bg="#110f18", fg="#00e87a"))
            
            # Botón del navegador (Deshabilitado)
            self.browser_btn.config(state="disabled", fg="#555555", bg="#0a0a0f")
            self.browser_btn.unbind("<Enter>")
            self.browser_btn.unbind("<Leave>")

    def toggle_server(self):
        if not self.is_running:
            try:
                self.server_thread = FlaskServerThread(app)
                self.server_thread.start()
                self.is_running = True
                
                # Actualizar UI
                self.status_label.config(text="Estado: Activo (Puerto 5001)", fg="#00e87a")
                self.update_button_styles()
                
                # Abrir navegador automáticamente al iniciar
                self.root.after(1000, self.open_browser)
            except Exception as e:
                tk.messagebox.showerror("Error", f"No se pudo iniciar el servidor:\n{str(e)}")
        else:
            self.stop_server()

    def stop_server(self):
        if self.is_running and self.server_thread:
            self.server_thread.shutdown()
            self.server_thread = None
            self.is_running = False
            
            # Actualizar UI
            self.status_label.config(text="Estado: Apagado", fg="#ef4444")
            self.update_button_styles()

    def open_browser(self):
        if self.is_running:
            webbrowser.open("http://127.0.0.1:5001")

    def on_closing(self):
        if self.is_running:
            self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    try:
        if getattr(sys, 'frozen', False):
            os.chdir(sys._MEIPASS)
            
        root = tk.Tk()
        app_gui = LauncherApp(root)
        root.mainloop()
    except Exception as e:
        log_crash(traceback.format_exc())
        sys.exit(1)
