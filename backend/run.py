from app import create_app
from flask_cors import CORS

app = create_app()
CORS(app, resources={r"/api/*": {"origins": "http://10.201.59.16:5173"}})

if __name__ == '__main__':
    app.run(debug=True) 