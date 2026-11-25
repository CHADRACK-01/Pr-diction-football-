"""Conteneur applicatif orienté objet pour Flask, Telegram et le démarrage."""

import threading
import time

from core.utils.logs import log_info, log_warning


class ApplicationRuntime:
    """Orchestre les services applicatifs sans les transformer en fonctions globales."""

    def __init__(
        self,
        *,
        app,
        bot,
        config,
        initialiser_bdd,
        scheduler_callback,
    ):
        self.app = app
        self.bot = bot
        self.config = config
        self.initialiser_bdd = initialiser_bdd
        self.scheduler_callback = scheduler_callback

    def register_routes(self):
        from web.routes_admin import register_admin_routes
        from web.routes_public import register_public_routes

        register_public_routes(
            self.app,
            bot=self.bot,
            initialiser_bdd_si_necessaire=self.initialiser_bdd,
        )
        register_admin_routes(
            self.app,
            config=self.config,
            initialiser_bdd_si_necessaire=self.initialiser_bdd,
        )
        return self

    def start_scheduler(self):
        if self.config.MODE_TEST:
            log_warning("MODE TEST ACTIVÉ : le scheduler est désactivé.", "BOOT")
            return self

        if self.config.MODE_VITRINE:
            log_warning("Mode vitrine : scheduler désactivé.", "BOOT")
            return self

        thread = threading.Thread(
            target=self._run_scheduler_after_delay,
            daemon=True,
            name="football-scheduler",
        )
        thread.start()
        log_info("Scheduler programmé.", "BOOT")
        return self

    def _run_scheduler_after_delay(self):
        time.sleep(60)
        self.scheduler_callback()

    def start(self):
        log_info("Bot prêt (Lazy Loading activé).", "BOOT")
        self.register_routes()
        self.start_scheduler()
        return self
