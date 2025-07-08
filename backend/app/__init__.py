from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://10.201.59.16:5173"],
            print(f"CORS origins configured: {["http://localhost:5173", "http://127.0.0.1:5173", "http://10.201.59.16:5173"]}")
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept"],
            "supports_credentials": True,
            "expose_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints here
    from .routes import main
    from .routes import database_routes
    app.register_blueprint(main.bp)
    app.register_blueprint(database_routes.bp)
    
    return app 