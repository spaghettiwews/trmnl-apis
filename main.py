from flask import Flask
from blueprints.photos import photos_bp
from blueprints.hackernews import hackernews_bp
from blueprints.todos import todos_bp
from blueprints.weather import weather_bp
from blueprints.merge import merge_bp
from blueprints.deutsch import deutsch_bp

def create_app():
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
