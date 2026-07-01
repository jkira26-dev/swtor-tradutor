import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import winreg

# Ensure build_patcher is packaged by PyInstaller by importing directly
import build_patcher


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de estilo
# ─────────────────────────────────────────────────────────────────────────────

COLORS = {
    "bg":           "#12141a",
    "surface":      "#1c1f2b",
    "surface2":     "#242838",
    "border":       "#2e3348",
    "accent":       "#4f8ef7",
    "accent_hover": "#3a77e8",
    "accent_dim":   "#2a4a8a",
    "success":      "#3ecf72",
    "warning":      "#f5a623",
    "error":        "#e05252",
    "text":         "#e8eaf2",
    "text_dim":     "#8890aa",
    "log_bg":       "#0d0f14",
    "log_fg":       "#7ee8a2",
    "log_info":     "#a0c4ff",
    "log_warn":     "#f5a623",
    "log_err":      "#e05252",
}

FONT_TITLE   = ("Segoe UI", 17, "bold")
FONT_SUB     = ("Segoe UI", 10)
FONT_LABEL   = ("Segoe UI", 9)
FONT_BUTTON  = ("Segoe UI", 10, "bold")
FONT_LOG     = ("Consolas", 9)
FONT_STATUS  = ("Segoe UI", 9)


# ─────────────────────────────────────────────────────────────────────────────
# Janela principal
# ─────────────────────────────────────────────────────────────────────────────

class TranslatorGUI(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("SWTOR Tradutor PT-BR")
        self.geometry("680x580")
        self.minsize(640, 540)
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)

        # Ícone da janela (tenta carregar se existir)
        self._try_set_icon()

        # Variáveis de estado
        self.game_path    = tk.StringVar()
        self.make_backup  = tk.BooleanVar(value=False)
        self._is_running  = False

        self.auto_detect_path()
        self._build_ui()
        self._configure_ttk_style()

    # ── Ícone ─────────────────────────────────────────────────────────────────

    def _try_set_icon(self):
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

    # ── Detecção automática ───────────────────────────────────────────────────

    def auto_detect_path(self):
        """Tenta detectar automaticamente a pasta do SWTOR."""
        common_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\Star Wars - The Old Republic",
            r"C:\Program Files\Steam\steamapps\common\Star Wars - The Old Republic",
            r"D:\SteamLibrary\steamapps\common\Star Wars - The Old Republic",
            r"E:\SteamLibrary\steamapps\common\Star Wars - The Old Republic",
        ]

        # Registro da Steam
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\WOW6432Node\Valve\Steam"
            )
            steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
            candidate = os.path.join(
                steam_path, "steamapps", "common",
                "Star Wars - The Old Republic"
            )
            if os.path.exists(candidate):
                self.game_path.set(candidate)
                return
        except (WindowsError, OSError):
            pass

        for path in common_paths:
            if os.path.exists(path):
                self.game_path.set(path)
                return

        self.game_path.set("")

    # ── Estilo ttk ────────────────────────────────────────────────────────────

    def _configure_ttk_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Progressbar
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor  = COLORS["surface2"],
            background   = COLORS["accent"],
            bordercolor  = COLORS["border"],
            lightcolor   = COLORS["accent"],
            darkcolor    = COLORS["accent"],
            thickness    = 16,
        )

        # Checkbutton
        style.configure(
            "Custom.TCheckbutton",
            background   = COLORS["surface"],
            foreground   = COLORS["text_dim"],
            font         = FONT_LABEL,
            focuscolor   = COLORS["surface"],
        )
        style.map(
            "Custom.TCheckbutton",
            background   = [("active", COLORS["surface"])],
            foreground   = [("active", COLORS["text"])],
        )

    # ── Construção da UI ──────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Cabeçalho ─────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLORS["surface"], pady=0)
        header.pack(fill=tk.X)

        header_inner = tk.Frame(header, bg=COLORS["surface"])
        header_inner.pack(padx=24, pady=16)

        tk.Label(
            header_inner,
            text="⚔  SWTOR Tradutor PT-BR",
            font=FONT_TITLE,
            bg=COLORS["surface"],
            fg=COLORS["accent"],
        ).pack(side=tk.LEFT)

        tk.Label(
            header_inner,
            text="v2.3",
            font=FONT_LABEL,
            bg=COLORS["surface"],
            fg=COLORS["text_dim"],
        ).pack(side=tk.LEFT, padx=(8, 0), anchor="s", pady=(0, 3))

        # Linha separadora
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill=tk.X)

        # ── Corpo ─────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        # Caminho do jogo
        tk.Label(
            body,
            text="Pasta de instalação do SWTOR:",
            font=FONT_LABEL,
            bg=COLORS["bg"],
            fg=COLORS["text_dim"],
        ).pack(anchor="w")

        path_frame = tk.Frame(body, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        path_frame.pack(fill=tk.X, pady=(4, 0))

        self._entry_path = tk.Entry(
            path_frame,
            textvariable=self.game_path,
            font=FONT_LABEL,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief=tk.FLAT,
            bd=6,
        )
        self._entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_browse = tk.Button(
            path_frame,
            text="Procurar",
            font=FONT_LABEL,
            bg=COLORS["surface2"],
            fg=COLORS["text"],
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            activebackground=COLORS["border"],
            activeforeground=COLORS["text"],
            command=self.browse_path,
        )
        btn_browse.pack(side=tk.RIGHT)

        # Opções
        opts_frame = tk.Frame(body, bg=COLORS["bg"])
        opts_frame.pack(fill=tk.X, pady=(10, 0))

        self._chk_backup = ttk.Checkbutton(
            opts_frame,
            text="Criar backup dos arquivos .tor antes de patchear  (pode ocupar vários GB)",
            variable=self.make_backup,
            style="Custom.TCheckbutton",
        )
        self._chk_backup.pack(anchor="w")

        # Botão instalar
        self._btn_install = tk.Button(
            body,
            text="INSTALAR TRADUÇÃO",
            font=FONT_BUTTON,
            bg=COLORS["accent"],
            fg="#ffffff",
            relief=tk.FLAT,
            bd=0,
            pady=10,
            cursor="hand2",
            activebackground=COLORS["accent_hover"],
            activeforeground="#ffffff",
            command=self.start_installation,
        )
        self._btn_install.pack(fill=tk.X, pady=(14, 0))

        # Barra de progresso + label de status
        progress_frame = tk.Frame(body, bg=COLORS["bg"])
        progress_frame.pack(fill=tk.X, pady=(10, 0))

        self._progress_var = tk.DoubleVar(value=0.0)
        self._progressbar = ttk.Progressbar(
            progress_frame,
            variable=self._progress_var,
            maximum=100.0,
            style="Custom.Horizontal.TProgressbar",
            mode="determinate",
        )
        self._progressbar.pack(fill=tk.X)

        status_row = tk.Frame(body, bg=COLORS["bg"])
        status_row.pack(fill=tk.X, pady=(4, 0))

        self._lbl_status = tk.Label(
            status_row,
            text="Aguardando...",
            font=FONT_STATUS,
            bg=COLORS["bg"],
            fg=COLORS["text_dim"],
            anchor="w",
        )
        self._lbl_status.pack(side=tk.LEFT)

        self._lbl_count = tk.Label(
            status_row,
            text="",
            font=FONT_STATUS,
            bg=COLORS["bg"],
            fg=COLORS["accent"],
            anchor="e",
        )
        self._lbl_count.pack(side=tk.RIGHT)

        # Área de log
        tk.Label(
            body,
            text="Log:",
            font=FONT_LABEL,
            bg=COLORS["bg"],
            fg=COLORS["text_dim"],
        ).pack(anchor="w", pady=(10, 2))

        log_frame = tk.Frame(body, bg=COLORS["log_bg"], highlightbackground=COLORS["border"], highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=FONT_LOG,
            bg=COLORS["log_bg"],
            fg=COLORS["log_fg"],
            relief=tk.FLAT,
            bd=8,
            state=tk.DISABLED,
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # Configurar tags de cor para o log
        self.log_area.tag_config("info",    foreground=COLORS["log_info"])
        self.log_area.tag_config("success", foreground=COLORS["success"])
        self.log_area.tag_config("warning", foreground=COLORS["warning"])
        self.log_area.tag_config("error",   foreground=COLORS["error"])
        self.log_area.tag_config("dim",     foreground=COLORS["text_dim"])

        self._log_raw("Pronto para instalar.\n", tag="dim")
        self._log_raw("Verifique o caminho do jogo e clique em INSTALAR TRADUÇÃO.\n", tag="dim")

        # Hover effects no botão instalar
        self._btn_install.bind("<Enter>", lambda e: self._btn_install.config(bg=COLORS["accent_hover"]) if not self._is_running else None)
        self._btn_install.bind("<Leave>", lambda e: self._btn_install.config(bg=COLORS["accent"]) if not self._is_running else None)

    # ── Logging ───────────────────────────────────────────────────────────────

    def _log_raw(self, message, tag=None):
        """Insere texto no log com tag de cor opcional (thread-safe via after)."""
        def _insert():
            self.log_area.config(state=tk.NORMAL)
            if tag:
                self.log_area.insert(tk.END, message + "\n", tag)
            else:
                self.log_area.insert(tk.END, message + "\n")
            self.log_area.see(tk.END)
            self.log_area.config(state=tk.DISABLED)
        self.after(0, _insert)

    def log(self, message):
        """Logger padrão passado ao build_patcher. Detecta prefixo para colorir."""
        tag = None
        msg_lower = message.lower()
        if "[ok]" in msg_lower or "sucesso" in msg_lower or "concluído" in msg_lower:
            tag = "success"
        elif "[erro]" in msg_lower or "falha" in msg_lower or "erro:" in msg_lower:
            tag = "error"
        elif "[aviso]" in msg_lower or "aviso" in msg_lower:
            tag = "warning"
        elif message.startswith("  >") or message.startswith("    "):
            tag = "dim"
        self._log_raw(message, tag=tag)

    # ── Progresso ─────────────────────────────────────────────────────────────

    def _on_progress(self, current, total):
        """Callback chamado pelo patcher a cada STB processado."""
        def _update():
            if total > 0:
                pct = (current / total) * 100.0
                self._progress_var.set(pct)
                self._lbl_count.config(text=f"{current} / {total} STBs")
        self.after(0, _update)

    def _on_file(self, filename):
        """Callback chamado ao iniciar processamento de um arquivo .tor."""
        def _update():
            self._lbl_status.config(text=f"Processando: {filename}", fg=COLORS["text"])
        self.after(0, _update)

    # ── Ações ─────────────────────────────────────────────────────────────────

    def browse_path(self):
        folder = filedialog.askdirectory(title="Selecione a pasta de instalação do SWTOR")
        if folder:
            self.game_path.set(folder)

    def start_installation(self):
        if self._is_running:
            return

        path = self.game_path.get().strip()
        if not path:
            messagebox.showerror("Erro", "Nenhum caminho informado.")
            return

        if not os.path.exists(os.path.join(path, "Assets")):
            messagebox.showerror(
                "Pasta inválida",
                "A pasta selecionada não parece ser a instalação do SWTOR.\n"
                "A subpasta 'Assets' não foi encontrada."
            )
            return

        self._is_running = True
        self._btn_install.config(
            state=tk.DISABLED,
            text="INSTALANDO...",
            bg=COLORS["accent_dim"],
        )
        self._progress_var.set(0.0)
        self._lbl_status.config(text="Iniciando...", fg=COLORS["text"])
        self._lbl_count.config(text="")

        # Limpar log
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)

        self.log("Iniciando instalação da tradução PT-BR...")

        thread = threading.Thread(
            target=self._run_installation_thread,
            args=(path, self.make_backup.get()),
            daemon=True,
        )
        thread.start()

    def _run_installation_thread(self, path, do_backup):
        try:
            success = build_patcher.run_patcher(
                path,
                logger       = self.log,
                on_progress  = self._on_progress,
                on_file      = self._on_file,
                make_backup  = do_backup,
            )
            if success:
                self.after(0, self._on_success)
            else:
                self.after(0, self._on_failure)
        except Exception as e:
            self.log(f"[ERRO] Erro crítico: {e}")
            self.after(0, lambda: self._on_failure(str(e)))

    def _on_success(self):
        self._lbl_status.config(text="Tradução aplicada com sucesso!", fg=COLORS["success"])
        self._btn_install.config(
            state=tk.NORMAL,
            text="INSTALAR TRADUÇÃO",
            bg=COLORS["accent"],
        )
        self._is_running = False
        messagebox.showinfo(
            "Sucesso! ⚔",
            "A tradução PT-BR foi aplicada com sucesso!\n\n"
            "Inicie o SWTOR normalmente — o jogo já estará em Português do Brasil."
        )

    def _on_failure(self, detail=""):
        self._lbl_status.config(text="Falha na instalação.", fg=COLORS["error"])
        self._btn_install.config(
            state=tk.NORMAL,
            text="INSTALAR TRADUÇÃO",
            bg=COLORS["accent"],
        )
        self._is_running = False
        if detail:
            messagebox.showerror("Falha", f"A instalação falhou:\n\n{detail}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = TranslatorGUI()
    app.mainloop()
