import threading
import logging
import pytz
from datetime import datetime

from plugins.plugin_registry import get_plugin_instance
from refresh_task import PlaylistRefresh


logger = logging.getLogger(__name__)


class DashboardRefreshTask:
    def __init__(
        self,
        device_config,
        playlist_name="Touchscreen",
        check_interval=60
    ):
        self.device_config = device_config
        self.playlist_name = playlist_name
        self.check_interval = check_interval

        self.thread = None
        self.running = False
        self.stop_event = threading.Event()


    def start(self):
        if self.thread and self.thread.is_alive():
            return

        logger.info(
            f"Starting dashboard refresh task for "
            f"playlist '{self.playlist_name}'"
        )

        self.running = True
        self.stop_event.clear()

        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )

        self.thread.start()


    def stop(self):
        self.running = False
        self.stop_event.set()

        if self.thread:
            self.thread.join()

        logger.info("Dashboard refresh task stopped")


    def _get_current_datetime(self):
        tz_str = self.device_config.get_config(
            "timezone",
            default="UTC"
        )

        return datetime.now(
            pytz.timezone(tz_str)
        )


    def _run(self):
        while self.running:
            try:
                self.refresh_due_plugins()

            except Exception:
                logger.exception(
                    "Exception during dashboard refresh"
                )

            self.stop_event.wait(
                timeout=self.check_interval
            )


    def refresh_due_plugins(self):
        playlist_manager = (
            self.device_config.get_playlist_manager()
        )

        playlist = playlist_manager.get_playlist(
            self.playlist_name
        )

        if not playlist:
            logger.warning(
                f"Dashboard playlist "
                f"'{self.playlist_name}' not found"
            )
            return

        current_dt = self._get_current_datetime()

        config_changed = False

        for plugin_instance in playlist.plugins:

            if not plugin_instance.should_refresh(
                current_dt
            ):
                continue

            logger.info(
                f"Dashboard image due for refresh. "
                f"| plugin_instance: "
                f"'{plugin_instance.name}'"
            )

            plugin_config = self.device_config.get_plugin(
                plugin_instance.plugin_id
            )

            if not plugin_config:
                logger.error(
                    f"Plugin config not found for "
                    f"'{plugin_instance.plugin_id}'"
                )
                continue

            try:
                plugin = get_plugin_instance(
                    plugin_config
                )

                refresh_action = PlaylistRefresh(
                    playlist,
                    plugin_instance
                )

                refresh_action.execute(
                    plugin,
                    self.device_config,
                    current_dt
                )

                config_changed = True

            except Exception:
                logger.exception(
                    f"Failed to refresh dashboard "
                    f"plugin '{plugin_instance.name}'"
                )

        if config_changed:
            self.device_config.write_config()
