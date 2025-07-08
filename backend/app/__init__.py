from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app)
    print(f"CORS origins configured: All origins allowed temporarily for debugging.")
    
    # Register blueprints here
    from .routes import main
    from .routes import database_routes
    app.register_blueprint(main.bp)
    app.register_blueprint(database_routes.bp)
    
    return app 