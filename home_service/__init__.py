from flask import Flask, jsonify
from flask import make_response, render_template
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix

from home_service.config import DevelopmentConfig
from home_service.core import exception_handler, create_response
from home_service.models.base import db
from home_service.endpoints import sensor_blueprint


def create_app():

    # Instantiate flask app
    app = Flask(__name__, instance_relative_config=True)

    # Set config
    app.config.from_object(DevelopmentConfig)

    # Register Database
    # db.metadata.clear()
    db.init_app(app)
    migrate = Migrate(app, db)

    # Proxy support for NGINX
    app.wsgi_app = ProxyFix(app.wsgi_app)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/_")
    def breakpoint():
        breakpoint()
        return " ", 200

    @app.route("/debug")
    def debug():
        return render_template("debug.html")

    app.register_blueprint(sensor_blueprint.sensor_blueprint)
    app.register_error_handler(Exception, exception_handler)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port="6969", debug=True)