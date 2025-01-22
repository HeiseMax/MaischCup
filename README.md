install requirements:
pip install -r requirements.txt

initialize the database:
(python)
with app.app_context():
    db.create_all()

run on localhost:
flask run

run on network:
flask run --host=0.0.0.0