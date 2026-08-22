from flask import Blueprint, render_template, current_app
from plugins.plugin_registry import get_plugin_instance
import os

dashboard_bp = Blueprint("dashboard", __name__)

def plugin_asset_url(plugin_id, path):
    """
    Convert an absolute plugin file path like:
      /home/qporter/proj/InkyPi/src/plugins/weather/icons/02d.png

    into a browser-accessible route like:
      /images/weather/icons/02d.png
    """

    normalized = path.replace("\\", "/")

    marker = f"/plugins/{plugin_id}/"

    if marker not in normalized:
        return path

    relative_path = normalized.split(marker, 1)[1]

    return f"/images/{plugin_id}/{relative_path}"

@dashboard_bp.route("/dashboard")
def dashboard():
    device_config = current_app.config["DEVICE_CONFIG"]
    playlist_manager = device_config.get_playlist_manager()

    # For now, use our known Weather instance.
    # Later this will come from dashboard configuration.
    weather_instance = playlist_manager.find_plugin(
        "weather",
        "Free Test"
    )

    if not weather_instance:
        return "Weather plugin instance 'Free Test' not found", 404

    plugin_config = device_config.get_plugin(
        weather_instance.plugin_id
    )

    if not plugin_config:
        return "Weather plugin configuration not found", 500

    weather_plugin = get_plugin_instance(plugin_config)

    weather_context = weather_plugin.get_render_context(
        weather_instance.settings,
        device_config
    )

    weather_context["current_day_icon"] = plugin_asset_url(
        "weather",
        weather_context["current_day_icon"]
    )

    for hour in weather_context.get("hourly_forecast", []):
        hour["icon"] = plugin_asset_url(
            "weather",
            hour["icon"]
        )

    for day in weather_context.get("forecast", []):
        day["icon"] = plugin_asset_url(
            "weather",
            day["icon"]
        )

        if day.get("moon_phase_icon"):
            day["moon_phase_icon"] = plugin_asset_url(
                "weather",
                day["moon_phase_icon"]
            )

    for data_point in weather_context.get("data_points", []):
        if data_point.get("icon"):
            data_point["icon"] = plugin_asset_url(
                "weather",
                data_point["icon"]
            )

    return render_template(
        "dashboard/dashboard.html",
        weather=weather_context
    )
