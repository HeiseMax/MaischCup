install requirements:
pip install -r requirements.txt

venv:
. .venv/bin/activate

initialize a database (name in app.config):
(python)
from app import app
from app import db
with app.app_context():
    db.create_all()

run on localhost:
flask run

run on network:
flask run --host=0.0.0.0

for debug mode:
--debug


create app: (creates app, but db does not work, doesnt create window to use or close, use pywebview)
pyinstaller -w -F --add-data "templates;templates" --add-data "static;static" app.py