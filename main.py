import logging
import os

from dotenv import load_dotenv

# Configure logging and env vars before blueprint imports so module-level
# logger.getLogger() calls and os.getenv() reads in each blueprint are correct.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
load_dotenv()

logger = logging.getLogger(__name__)

from flask import Flask
from blueprints.photos import photos_bp
from blueprints.hackernews import hackernews_bp
from blueprints.todos import todos_bp
from blueprints.weather import weather_bp
from blueprints.merge import merge_bp
from blueprints.deutsch import deutsch_bp

_PHOTOS_VARS = ["BASE_PHOTOS_API_URL", "API_KEY", "ALBUM_ID"]
_CALENDAR_VARS = ["CALENDAR_URL", "CALENDAR_USER", "CALENDAR_PASSWORD", "CALENDAR_ID"]


def create_app():
    missing_photos = [v for v in _PHOTOS_VARS if not os.getenv(v)]
    missing_calendar = [v for v in _CALENDAR_VARS if not os.getenv(v)]

    if missing_photos:
        logger.warning(f"Photos API will be unavailable — missing env vars: {missing_photos}")
    if missing_calendar:
        logger.warning(f"Calendar/todos API will be unavailable — missing env vars: {missing_calendar}")

    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.register_blueprint(photos_bp, url_prefix='/')
    app.register_blueprint(hackernews_bp, url_prefix='/')
    app.register_blueprint(todos_bp, url_prefix='/')
    app.register_blueprint(weather_bp, url_prefix='/')
    app.register_blueprint(merge_bp, url_prefix='/')
    app.register_blueprint(deutsch_bp, url_prefix='/')

    @app.route('/')
    def index():
        return 'ok'

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
