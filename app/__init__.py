import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify, request
from app.models import db


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'devops-soc-incident-sec-key-2026')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_VERSION = '1.0.0'
    APP_NAME = 'Security Incident Case Management System'


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'incidents_dev.db')}"
    )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'incidents.db')}"
    )


CONFIG_MAP = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def configure_logging(app):
    """Sets up structured application logging for DevOps observability."""
    log_level = logging.INFO
    if app.config.get('DEBUG'):
        log_level = logging.DEBUG

    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s in %(filename)s:%(lineno)d] - %(message)s'
    )

    # Console handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    app.logger.handlers.clear()
    app.logger.addHandler(stream_handler)

    # File handler (only if not in testing mode)
    if not app.config.get('TESTING'):
        log_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(log_level)
    app.logger.info(f"Initialized {app.config['APP_NAME']} in {app.config.get('ENV_NAME', 'default')} mode")


def create_app(config_name=None):
    """Flask application factory."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development').lower()

    app = Flask(__name__)
    config_class = CONFIG_MAP.get(config_name, DevelopmentConfig)
    app.config.from_object(config_class)
    app.config['ENV_NAME'] = config_name

    # Ensure instance directory exists
    instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Configure logging
    configure_logging(app)

    # Register routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 Not Found: {request.path}")
        if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
            return jsonify({'error': 'Resource not found', 'path': request.path, 'status_code': 404}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 Internal Error on {request.path}: {str(error)}", exc_info=True)
        db.session.rollback()
        if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
            return jsonify({'error': 'Internal server anomaly', 'status_code': 500}), 500
        return render_template('errors/500.html'), 500

    return app
