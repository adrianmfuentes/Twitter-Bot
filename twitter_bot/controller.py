"""Wires the view to the model and keeps API calls off the Tkinter thread."""
import logging
import threading
from typing import Callable

from . import config
from .errors import TwitterBotError
from .model import TwitterModel
from .view import TwitterBotView

logger = logging.getLogger(__name__)


class TwitterBotController:
    def __init__(self):
        self.model: TwitterModel | None = None
        self.view = TwitterBotView(self)
        self._try_prefill_saved_credentials()

    # ------------------------------------------------------------------
    def run_async(self, work: Callable, on_success: Callable = None, on_error: Callable = None):
        """Run `work` on a background thread, then hop back to the Tk thread."""

        def target():
            try:
                result = work()
            except Exception as exc:  # noqa: BLE001 - surfaced to the UI, not swallowed
                logger.exception("Background task failed")
                if on_error:
                    self.view.root.after(0, on_error, exc)
                return
            if on_success:
                self.view.root.after(0, on_success, result)

        threading.Thread(target=target, daemon=True).start()

    def _error_message(self, exc: Exception) -> str:
        return str(exc) if isinstance(exc, TwitterBotError) else f"Error inesperado: {exc}"

    # -- Credential prefill -------------------------------------------------
    def _try_prefill_saved_credentials(self):
        creds = config.load_from_env() or config.load_from_keyring()
        if creds:
            self.view.prefill_login(creds)

    # -- Login ------------------------------------------------------------
    def login(self):
        login_data = self.view.get_login_data()
        if not all(login_data.values()):
            self.view.show_message("Aviso", "Todos los campos son obligatorios.", "warning")
            return

        self.view.set_login_busy(True, "Verificando credenciales...")

        def work():
            model = TwitterModel(**login_data)
            me = model.verify_credentials()
            return model, me

        def on_success(result):
            model, me = result
            self.model = model
            if self.view.remember_var.get():
                config.save_to_keyring(config.Credentials(**login_data))
            self.view.set_login_busy(False)
            self.view.build_main_screen(me.username)
            self.view.set_status(f"Sesión iniciada como @{me.username}.", "success")

        def on_error(exc):
            self.view.set_login_busy(False, "")
            self.view.show_message("Error de acceso", self._error_message(exc), "error")

        self.run_async(work, on_success, on_error)

    def logout(self):
        self.model = None
        self.view._build_login_screen()

    def forget_credentials(self):
        config.clear_keyring()
        self.view.show_message("Listo", "Se olvidaron las credenciales guardadas en este equipo.")

    # -- Compose ------------------------------------------------------------
    def send_tweet(self):
        message = self.view.get_tweet_message()
        if not message:
            self.view.show_message("Aviso", "El tweet no puede estar vacío.", "warning")
            return
        if len(message) > 280:
            self.view.show_message("Aviso", "El tweet supera los 280 caracteres.", "warning")
            return

        media_path = self.view.media_path
        self.view.set_compose_busy(True)

        def on_success(_result):
            self.view.set_compose_busy(False)
            self.view.clear_compose()
            self.view.set_status("Tweet publicado.", "success")

        def on_error(exc):
            self.view.set_compose_busy(False)
            self.view.set_status("No se pudo publicar el tweet.", "error")
            self.view.show_message("Error", self._error_message(exc), "error")

        self.run_async(lambda: self.model.tweet(message, media_path), on_success, on_error)

    # -- Timeline -----------------------------------------------------------
    def load_timeline(self):
        self.view.set_status("Cargando tus tweets...", "info")

        def on_success(tweets):
            self.view.load_timeline_rows(tweets)
            self.view.set_status(f"{len(tweets)} tweets cargados.", "success")

        def on_error(exc):
            self.view.set_status("No se pudo cargar la línea de tiempo.", "error")
            self.view.show_message("Error", self._error_message(exc), "error")

        self.run_async(lambda: self.model.get_recent_tweets(max_results=20), on_success, on_error)

    def delete_selected_tweet(self):
        tweet_id = self.view.get_selected_timeline_tweet_id()
        if not tweet_id:
            self.view.show_message("Aviso", "Selecciona un tweet primero.", "warning")
            return

        def on_success(_result):
            self.view.set_status("Tweet eliminado.", "success")
            self.load_timeline()

        def on_error(exc):
            self.view.show_message("Error", self._error_message(exc), "error")

        self.run_async(lambda: self.model.delete_tweet(tweet_id), on_success, on_error)

    # -- Search -------------------------------------------------------------
    def search_tweets(self):
        query = self.view.get_search_query()
        if not query:
            self.view.show_message("Aviso", "Escribe una palabra clave para buscar.", "warning")
            return
        self.view.set_status(f"Buscando '{query}'...", "info")

        def on_success(tweets):
            self.view.load_search_rows(tweets)
            self.view.set_status(f"{len(tweets)} resultados para '{query}'.", "success")

        def on_error(exc):
            self.view.set_status("La búsqueda falló.", "error")
            self.view.show_message("Error", self._error_message(exc), "error")

        self.run_async(lambda: self.model.search_tweets(query, max_results=20), on_success, on_error)

    def like_selected_search_result(self):
        tweet_id = self.view.get_selected_search_tweet_id()
        if not tweet_id:
            self.view.show_message("Aviso", "Selecciona un tweet de los resultados.", "warning")
            return
        self.run_async(
            lambda: self.model.like_tweet(tweet_id),
            lambda _r: self.view.set_status("Marcado como me gusta.", "success"),
            lambda exc: self.view.show_message("Error", self._error_message(exc), "error"),
        )

    def retweet_selected_search_result(self):
        tweet_id = self.view.get_selected_search_tweet_id()
        if not tweet_id:
            self.view.show_message("Aviso", "Selecciona un tweet de los resultados.", "warning")
            return
        self.run_async(
            lambda: self.model.retweet(tweet_id),
            lambda _r: self.view.set_status("Retweet realizado.", "success"),
            lambda exc: self.view.show_message("Error", self._error_message(exc), "error"),
        )

    # -- Bulk engagement --------------------------------------------------
    def like_by_keyword(self):
        keyword, count = self.view.get_bulk_like_inputs()
        if not keyword or count <= 0:
            self.view.show_message("Aviso", "Indica una palabra clave y una cantidad válida.", "warning")
            return

        self.view.set_bulk_busy(True)
        self.view.reset_bulk_progress(count)

        def on_result(result):
            status = "OK" if result.ok else f"ERROR: {result.error}"
            self.view.root.after(0, self.view.append_bulk_log, f"{result.tweet_id}: {status}")

        def on_success(results):
            self.view.set_bulk_busy(False)
            ok_count = sum(1 for r in results if r.ok)
            self.view.set_status(f"{ok_count}/{len(results)} tweets marcados como me gusta.", "success")

        def on_error(exc):
            self.view.set_bulk_busy(False)
            self.view.show_message("Error", self._error_message(exc), "error")

        self.run_async(
            lambda: self.model.like_tweets_by_keyword(keyword, count=count, on_result=on_result),
            on_success,
            on_error,
        )

    def follow_user(self):
        username = self.view.get_follow_username()
        if not username:
            self.view.show_message("Aviso", "Indica un nombre de usuario.", "warning")
            return
        self.run_async(
            lambda: self.model.follow_user(username),
            lambda _r: self.view.set_status(f"Ahora sigues a @{username}.", "success"),
            lambda exc: self.view.show_message("Error", self._error_message(exc), "error"),
        )

    def unfollow_user(self):
        username = self.view.get_follow_username()
        if not username:
            self.view.show_message("Aviso", "Indica un nombre de usuario.", "warning")
            return
        self.run_async(
            lambda: self.model.unfollow_user(username),
            lambda _r: self.view.set_status(f"Dejaste de seguir a @{username}.", "success"),
            lambda exc: self.view.show_message("Error", self._error_message(exc), "error"),
        )
