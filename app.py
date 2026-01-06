from flask import Flask
from flask_session import Session
from models import db
from routes import bp

app = Flask(__name__)

app.secret_key = 'supersecretkey'  # Needed for flashing messages
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fencing.db' #'sqlite:///maisch2025_03.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

db.init_app(app)
Session(app)

app.register_blueprint(bp)

if __name__ == '__main__':
    app.run(debug=True)
