"""Tkinter/ttkbootstrap GUI for the Twitter Bot.

The view only knows how to draw widgets and read/write their values; all
business logic (API calls, threading) lives in the controller.
"""
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, LEFT, RIGHT, X, Y, W

try:
    from PIL import Image, ImageTk
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

TWEET_MAX_LEN = 280
LIGHT_THEME = "flatly"
DARK_THEME = "darkly"


class TwitterBotView:
    def __init__(self, controller):
        self.controller = controller
        self.root = tb.Window(title="Twitter Bot", themename=LIGHT_THEME, resizable=(False, False))
        self.style = self.root.style
        self.media_path = None
        self._build_login_screen()

    # ------------------------------------------------------------------
    # Login screen
    # ------------------------------------------------------------------
    def _build_login_screen(self):
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title("Twitter Bot")
        self.root.resizable(False, False)
        self.root.geometry("420x420")

        frame = tb.Frame(self.root, padding=24)
        frame.pack(fill=BOTH, expand=True)

        tb.Label(frame, text="Twitter Bot", font=("Segoe UI", 18, "bold")).pack(pady=(0, 16))

        self.consumer_key_entry = self._labeled_entry(frame, "Consumer Key")
        self.consumer_secret_entry = self._labeled_entry(frame, "Consumer Secret", secret=True)
        self.access_token_entry = self._labeled_entry(frame, "Access Token")
        self.access_token_secret_entry = self._labeled_entry(frame, "Access Token Secret", secret=True)

        self.remember_var = tk.BooleanVar(value=False)
        tb.Checkbutton(
            frame, text="Recordar credenciales en este equipo", variable=self.remember_var
        ).pack(anchor=W, pady=(4, 12))

        self.login_button = tb.Button(
            frame, text="Iniciar sesión", bootstyle="primary", command=self.controller.login
        )
        self.login_button.pack(fill=X, pady=(0, 8))

        self.login_status = tb.Label(frame, text="", bootstyle="secondary")
        self.login_status.pack()

    def _labeled_entry(self, parent, label, secret=False):
        tb.Label(parent, text=label).pack(anchor=W)
        entry = tb.Entry(parent, show="*" if secret else "")
        entry.pack(fill=X, pady=(0, 10))
        return entry

    def prefill_login(self, creds):
        self.consumer_key_entry.insert(0, creds.consumer_key)
        self.consumer_secret_entry.insert(0, creds.consumer_secret)
        self.access_token_entry.insert(0, creds.access_token)
        self.access_token_secret_entry.insert(0, creds.access_token_secret)
        self.remember_var.set(True)

    def get_login_data(self) -> dict:
        return {
            "consumer_key": self.consumer_key_entry.get().strip(),
            "consumer_secret": self.consumer_secret_entry.get().strip(),
            "access_token": self.access_token_entry.get().strip(),
            "access_token_secret": self.access_token_secret_entry.get().strip(),
        }

    def set_login_busy(self, busy: bool, message: str = ""):
        self.login_button.configure(state=tk.DISABLED if busy else tk.NORMAL)
        self.login_status.configure(text=message)

    # ------------------------------------------------------------------
    # Main screen
    # ------------------------------------------------------------------
    def build_main_screen(self, username: str):
        for child in self.root.winfo_children():
            child.destroy()
        self.root.resizable(True, True)
        self.root.geometry("760x620")
        self.root.title(f"Twitter Bot — @{username}")

        notebook = tb.Notebook(self.root, padding=8)
        notebook.pack(fill=BOTH, expand=True)

        self._build_compose_tab(notebook)
        self._build_timeline_tab(notebook)
        self._build_search_tab(notebook)
        self._build_engagement_tab(notebook)
        self._build_settings_tab(notebook)

        self.status_bar = tb.Label(self.root, text="Listo.", anchor=W, bootstyle="secondary", padding=(10, 4))
        self.status_bar.pack(fill=X, side="bottom")

    # -- Compose ----------------------------------------------------------
    def _build_compose_tab(self, notebook):
        tab = tb.Frame(notebook, padding=16)
        notebook.add(tab, text="Publicar")

        tb.Label(tab, text="¿Qué está pasando?", font=("Segoe UI", 11, "bold")).pack(anchor=W)
        self.tweet_text = tk.Text(tab, height=5, wrap="word", font=("Segoe UI", 10))
        self.tweet_text.pack(fill=X, pady=(6, 2))
        self.tweet_text.bind("<KeyRelease>", self._update_char_counter)

        self.char_counter = tb.Label(tab, text=f"0 / {TWEET_MAX_LEN}", bootstyle="secondary")
        self.char_counter.pack(anchor="e")

        media_row = tb.Frame(tab)
        media_row.pack(fill=X, pady=(8, 0))
        tb.Button(media_row, text="Adjuntar imagen", bootstyle="secondary-outline",
                  command=self._pick_media).pack(side=LEFT)
        self.media_label = tb.Label(media_row, text="Sin imagen adjunta", bootstyle="secondary")
        self.media_label.pack(side=LEFT, padx=10)
        self.media_thumb_label = tb.Label(tab)
        self.media_thumb_label.pack(anchor=W, pady=6)

        self.send_button = tb.Button(
            tab, text="Publicar Tweet", bootstyle="primary", command=self._on_send_tweet
        )
        self.send_button.pack(fill=X, pady=(12, 0))

    def _update_char_counter(self, _event=None):
        length = len(self.get_tweet_message())
        self.char_counter.configure(text=f"{length} / {TWEET_MAX_LEN}")
        self.char_counter.configure(bootstyle="danger" if length > TWEET_MAX_LEN else "secondary")

    def _pick_media(self):
        path = filedialog.askopenfilename(
            title="Elegir imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif")],
        )
        if not path:
            return
        self.media_path = path
        self.media_label.configure(text=path.split("/")[-1].split("\\")[-1])
        self._show_thumbnail(path)

    def _show_thumbnail(self, path):
        if not HAS_PILLOW:
            return
        image = Image.open(path)
        image.thumbnail((120, 120))
        self._thumb_ref = ImageTk.PhotoImage(image)
        self.media_thumb_label.configure(image=self._thumb_ref)

    def _on_send_tweet(self):
        self.controller.send_tweet()

    def get_tweet_message(self) -> str:
        return self.tweet_text.get("1.0", "end").strip()

    def clear_compose(self):
        self.tweet_text.delete("1.0", "end")
        self.media_path = None
        self.media_label.configure(text="Sin imagen adjunta")
        self.media_thumb_label.configure(image="")
        self._update_char_counter()

    def set_compose_busy(self, busy: bool):
        self.send_button.configure(state=tk.DISABLED if busy else tk.NORMAL)

    # -- Timeline ---------------------------------------------------------
    def _build_timeline_tab(self, notebook):
        tab = tb.Frame(notebook, padding=16)
        notebook.add(tab, text="Mis Tweets")

        toolbar = tb.Frame(tab)
        toolbar.pack(fill=X, pady=(0, 8))
        tb.Button(toolbar, text="Actualizar", bootstyle="secondary-outline",
                  command=self.controller.load_timeline).pack(side=LEFT)
        tb.Button(toolbar, text="Eliminar seleccionado", bootstyle="danger-outline",
                  command=self.controller.delete_selected_tweet).pack(side=LEFT, padx=6)

        self.timeline_tree = self._make_tweet_tree(tab, columns=("fecha", "texto", "likes", "rts"))
        self.timeline_tree.heading("likes", text="Me gusta")
        self.timeline_tree.heading("rts", text="RTs")
        self.timeline_tree.column("likes", width=70, anchor="center")
        self.timeline_tree.column("rts", width=70, anchor="center")

    def load_timeline_rows(self, tweets):
        self.timeline_tree.delete(*self.timeline_tree.get_children())
        for t in tweets:
            metrics = getattr(t, "public_metrics", None) or {}
            created = getattr(t, "created_at", None)
            self.timeline_tree.insert(
                "", "end", iid=str(t.id),
                values=(
                    created.strftime("%Y-%m-%d %H:%M") if created else "",
                    t.text,
                    metrics.get("like_count", 0),
                    metrics.get("retweet_count", 0),
                ),
            )

    def get_selected_timeline_tweet_id(self):
        selection = self.timeline_tree.selection()
        return selection[0] if selection else None

    # -- Search -------------------------------------------------------------
    def _build_search_tab(self, notebook):
        tab = tb.Frame(notebook, padding=16)
        notebook.add(tab, text="Buscar")

        search_row = tb.Frame(tab)
        search_row.pack(fill=X, pady=(0, 8))
        self.search_entry = tb.Entry(search_row)
        self.search_entry.pack(side=LEFT, fill=X, expand=True)
        tb.Button(search_row, text="Buscar", bootstyle="primary",
                  command=self.controller.search_tweets).pack(side=LEFT, padx=(6, 0))

        self.search_tree = self._make_tweet_tree(tab, columns=("fecha", "texto"))

        action_row = tb.Frame(tab)
        action_row.pack(fill=X, pady=(8, 0))
        tb.Button(action_row, text="Me gusta", bootstyle="success-outline",
                  command=self.controller.like_selected_search_result).pack(side=LEFT)
        tb.Button(action_row, text="Retweet", bootstyle="info-outline",
                  command=self.controller.retweet_selected_search_result).pack(side=LEFT, padx=6)

    def get_search_query(self) -> str:
        return self.search_entry.get().strip()

    def load_search_rows(self, tweets):
        self.search_tree.delete(*self.search_tree.get_children())
        for t in tweets:
            created = getattr(t, "created_at", None)
            self.search_tree.insert(
                "", "end", iid=str(t.id),
                values=(created.strftime("%Y-%m-%d %H:%M") if created else "", t.text),
            )

    def get_selected_search_tweet_id(self):
        selection = self.search_tree.selection()
        return selection[0] if selection else None

    def _make_tweet_tree(self, parent, columns):
        tree = tb.Treeview(parent, columns=columns, show="headings", height=14)
        tree.heading("fecha", text="Fecha")
        tree.heading("texto", text="Tweet")
        tree.column("fecha", width=130, anchor="center")
        tree.column("texto", width=380, anchor=W)
        tree.pack(fill=BOTH, expand=True)
        return tree

    # -- Engagement -----------------------------------------------------------
    def _build_engagement_tab(self, notebook):
        tab = tb.Frame(notebook, padding=16)
        notebook.add(tab, text="Interacciones")

        bulk = tb.Labelframe(tab, text="Me gusta masivo por palabra clave", padding=12)
        bulk.pack(fill=X, pady=(0, 16))

        row = tb.Frame(bulk)
        row.pack(fill=X)
        tb.Label(row, text="Palabra clave:").pack(side=LEFT)
        self.bulk_keyword_entry = tb.Entry(row)
        self.bulk_keyword_entry.pack(side=LEFT, fill=X, expand=True, padx=6)
        tb.Label(row, text="Cantidad:").pack(side=LEFT)
        self.bulk_count_spin = tb.Spinbox(row, from_=1, to=50, width=5)
        self.bulk_count_spin.set(10)
        self.bulk_count_spin.pack(side=LEFT, padx=6)
        self.bulk_run_button = tb.Button(
            row, text="Ejecutar", bootstyle="primary", command=self.controller.like_by_keyword
        )
        self.bulk_run_button.pack(side=LEFT)

        self.bulk_progress = tb.Progressbar(bulk, mode="determinate")
        self.bulk_progress.pack(fill=X, pady=(10, 4))
        self.bulk_log = tk.Listbox(bulk, height=6)
        self.bulk_log.pack(fill=BOTH, expand=True)

        follow = tb.Labelframe(tab, text="Seguir / Dejar de seguir", padding=12)
        follow.pack(fill=X)
        frow = tb.Frame(follow)
        frow.pack(fill=X)
        tb.Label(frow, text="@usuario:").pack(side=LEFT)
        self.follow_username_entry = tb.Entry(frow)
        self.follow_username_entry.pack(side=LEFT, fill=X, expand=True, padx=6)
        tb.Button(frow, text="Seguir", bootstyle="success-outline",
                  command=self.controller.follow_user).pack(side=LEFT, padx=(0, 4))
        tb.Button(frow, text="Dejar de seguir", bootstyle="danger-outline",
                  command=self.controller.unfollow_user).pack(side=LEFT)

    def get_bulk_like_inputs(self):
        return self.bulk_keyword_entry.get().strip(), int(self.bulk_count_spin.get() or 0)

    def get_follow_username(self) -> str:
        return self.follow_username_entry.get().strip()

    def reset_bulk_progress(self, maximum: int):
        self.bulk_log.delete(0, "end")
        self.bulk_progress.configure(maximum=max(maximum, 1), value=0)

    def append_bulk_log(self, text: str):
        self.bulk_log.insert("end", text)
        self.bulk_log.see("end")
        self.bulk_progress.step(1)

    def set_bulk_busy(self, busy: bool):
        self.bulk_run_button.configure(state=tk.DISABLED if busy else tk.NORMAL)

    # -- Settings ---------------------------------------------------------
    def _build_settings_tab(self, notebook):
        tab = tb.Frame(notebook, padding=16)
        notebook.add(tab, text="Ajustes")

        tb.Label(tab, text="Apariencia", font=("Segoe UI", 11, "bold")).pack(anchor=W)
        self.dark_mode_var = tk.BooleanVar(value=False)
        tb.Checkbutton(
            tab, text="Modo oscuro", variable=self.dark_mode_var,
            bootstyle="round-toggle", command=self._toggle_theme,
        ).pack(anchor=W, pady=(4, 20))

        tb.Label(tab, text="Cuenta", font=("Segoe UI", 11, "bold")).pack(anchor=W)
        tb.Button(tab, text="Olvidar credenciales guardadas", bootstyle="warning-outline",
                  command=self.controller.forget_credentials).pack(anchor=W, pady=(6, 4))
        tb.Button(tab, text="Cerrar sesión", bootstyle="danger-outline",
                  command=self.controller.logout).pack(anchor=W)

    def _toggle_theme(self):
        self.style.theme_use(DARK_THEME if self.dark_mode_var.get() else LIGHT_THEME)

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def set_status(self, message: str, level: str = "info"):
        bootstyle = {"info": "secondary", "success": "success", "error": "danger", "warning": "warning"}
        stamp = datetime.now().strftime("%H:%M:%S")
        if hasattr(self, "status_bar"):
            self.status_bar.configure(text=f"[{stamp}] {message}", bootstyle=bootstyle.get(level, "secondary"))

    def show_message(self, title, message, type_="info"):
        if type_ == "info":
            messagebox.showinfo(title, message)
        elif type_ == "warning":
            messagebox.showwarning(title, message)
        elif type_ == "error":
            messagebox.showerror(title, message)
