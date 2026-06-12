from flask import Flask
from app.config.settings import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here (e.g. SQLAlchemy)
    # db.init_app(app)

    # Register Blueprints
    from app.modules.auth.routes import auth_bp
    from app.modules.users.routes import users_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')

    @app.route('/health')
    def health_check():
        return {"status": "ok", "message": "API is running"}

    return app
