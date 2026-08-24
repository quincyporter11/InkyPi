from flask import Blueprint, render_template, current_app

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    device_config = current_app.config["DEVICE_CONFIG"]
    playlist_manager = device_config.get_playlist_manager()

    ### for now pull default playlist
    playlist = playlist_manager.get_playlist("Touchscreen")

    if not playlist:
        return "Dashboard playlist not found", 404

    pages = []

    for plugin_instance in playlist.plugins:
        pages.append({
            "playlist_name": playlist.name,
            "plugin_id": plugin_instance.plugin_id,
            "instance_name": plugin_instance.name,
        })

    return render_template(
        "dashboard/dashboard.html",
        pages=pages
    )
