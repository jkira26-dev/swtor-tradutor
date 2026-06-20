import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import winreg

# Ensure build_patcher is packaged by PyInstaller by importing directly
import build_patcher

class TranslatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SWTOR - Tradutor PT-BR")
        self.geometry("600x450")
        self.configure(bg="#1e1e1e")
        self.resizable(False, False)

        # Style colors
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#007acc"
        self.btn_bg = "#333333"
        self.btn_hover = "#444444"

        self.game_path = tk.StringVar()
        self.auto_detect_path()

        self.create_widgets()

    def auto_detect_path(self):
        """Tenta detectar automaticamente a pasta do SWTOR via Registro do Windows"""
        possible_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\Star Wars - The Old Republic",
            r"C:\Program Files\Steam\steamapps\common\Star Wars - The Old Republic",
            r"D:\SteamLibrary\steamapps\common\Star Wars - The Old Republic"
        ]
        
        # Tentativa pelo registro da Steam
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
            steam_game_path = os.path.join(steam_path, "steamapps", "common", "Star Wars - The Old Republic")
            if os.path.exists(steam_game_path):
                self.game_path.set(steam_game_path)
                return
        except WindowsError:
            pass
            
        # Verificar caminhos comuns
        for path in possible_paths:
            if os.path.exists(path):
                self.game_path.set(path)
                return
                
        self.game_path.set("Caminho não encontrado. Selecione manualmente.")

    def create_widgets(self):
        # Título
        lbl_title = tk.Label(self, text="Instalador de Tradução SWTOR", font=("Segoe UI", 16, "bold"), bg=self.bg_color, fg=self.accent_color)
        lbl_title.pack(pady=15)

        # Frame de Caminho
        frame_path = tk.Frame(self, bg=self.bg_color)
        frame_path.pack(fill=tk.X, padx=20, pady=5)

        lbl_path = tk.Label(frame_path, text="Pasta do Jogo:", font=("Segoe UI", 10), bg=self.bg_color, fg=self.fg_color)
        lbl_path.pack(side=tk.LEFT)

        entry_path = tk.Entry(frame_path, textvariable=self.game_path, width=50, font=("Segoe UI", 9), bg="#2d2d2d", fg=self.fg_color, insertbackground=self.fg_color, relief=tk.FLAT)
        entry_path.pack(side=tk.LEFT, padx=10, ipady=4)

        btn_browse = tk.Button(frame_path, text="Procurar...", font=("Segoe UI", 9), bg=self.btn_bg, fg=self.fg_color, relief=tk.FLAT, command=self.browse_path, cursor="hand2")
        btn_browse.pack(side=tk.LEFT, ipady=2, ipadx=5)

        # Botão de Instalar
        self.btn_install = tk.Button(self, text="INSTALAR TRADUÇÃO", font=("Segoe UI", 12, "bold"), bg=self.accent_color, fg="#ffffff", relief=tk.FLAT, command=self.start_installation, cursor="hand2")
        self.btn_install.pack(pady=20, ipadx=20, ipady=5)

        # Log Area
        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=70, height=12, font=("Consolas", 9), bg="#000000", fg="#00ff00", relief=tk.FLAT)
        self.log_area.pack(padx=20, pady=5)
        self.log_area.insert(tk.END, "Pronto para instalar.\nVerifique o caminho do jogo e clique em Instalar.\n")
        self.log_area.config(state=tk.DISABLED)

    def browse_path(self):
        folder = filedialog.askdirectory(title="Selecione a pasta do SWTOR")
        if folder:
            self.game_path.set(folder)

    def log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.update_idletasks()

    def start_installation(self):
        path = self.game_path.get()
        if not os.path.exists(os.path.join(path, "Assets")):
            messagebox.showerror("Erro", "A pasta selecionada não parece ser a instalação do SWTOR. Faltando a pasta 'Assets'.")
            return

        self.btn_install.config(state=tk.DISABLED, text="INSTALANDO...", bg="#555555")
        
        # Limpar logs
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)
        
        self.log("Iniciando a instalação da tradução...")
        
        # Executar em thread separada para não travar a GUI
        thread = threading.Thread(target=self.run_installation_thread, args=(path,))
        thread.daemon = True
        thread.start()

    def run_installation_thread(self, path):
        try:
            success = build_patcher.run_patcher(path, logger=self.log)
            if success:
                self.log("\n*** TRADUÇÃO CONCLUÍDA COM SUCESSO! ***")
                messagebox.showinfo("Sucesso", "A tradução foi aplicada com sucesso!")
            else:
                self.log("\n*** FALHA NA INSTALAÇÃO ***")
        except Exception as e:
            self.log(f"\nErro crítico durante a instalação: {e}")
            messagebox.showerror("Erro", f"Ocorreu um erro:\n{e}")
        finally:
            self.btn_install.config(state=tk.NORMAL, text="INSTALAR TRADUÇÃO", bg=self.accent_color)

if __name__ == "__main__":
    app = TranslatorGUI()
    app.mainloop()
