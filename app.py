from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = 'supersecretkey'  # Needed for flashing messages
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fencing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Define the Player model
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# Define the Score model
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    score1 = db.Column(db.Integer, nullable=False)
    score2 = db.Column(db.Integer, nullable=False)
    win = db.Column(db.Boolean, nullable=False)

    player1 = db.relationship('Player', foreign_keys=[player1_id])
    player2 = db.relationship('Player', foreign_keys=[player2_id])

# Function to calculate won matches
def calculate_won_matches(player_id):
    return Score.query.filter_by(player1_id=player_id, win=True).count()

# Function to calculate lost matches
def calculate_lost_matches(player_id):
    return Score.query.filter_by(player1_id=player_id, win=False).count()

# Function to calculate remaining matches
def calculate_remaining_matches(player_id):
    return Player.query.count() - 1 - Score.query.filter_by(player1_id=player_id).count()

# Home route
@app.route('/')
def index():
    players = Player.query.all()
    scores = Score.query.all()
    won_matches = {player.id: calculate_won_matches(player.id) for player in players}
    lost_matches = {player.id: calculate_lost_matches(player.id) for player in players}
    remaining_matches = {player.id: calculate_remaining_matches(player.id) for player in players}
    return render_template('index.html', players=players, scores=scores, won_matches=won_matches, lost_matches=lost_matches, remaining_matches=remaining_matches)

# Route to handle adding a new player
@app.route('/add_player', methods=['POST', 'GET'])
def add_player():
    if request.method == 'GET':
        return render_template('login.html')
    
    if request.method == 'POST':
        new_name = request.form['name']
        if Player.query.filter_by(name=new_name).first():
            session['player_id'] = Player.query.filter_by(name=new_name).first().id
            flash('Name already used. Please choose a different name.')
        else:
            new_player = Player(name=new_name)
            db.session.add(new_player)
            db.session.commit()
            session['player_id'] = new_player.id
            return redirect(url_for('index'))
        return redirect(url_for('add_player'))

# Route to handle score updates
@app.route('/update_score', methods=['GET', 'POST'])
def update_score():
    if request.method == 'GET':
        players = Player.query.all()
        scores = Score.query.all()
        return render_template('update_score.html', players=players, scores=scores)
    
    if request.method == 'POST':
        player1_id = int(request.form['player1_id'])
        player2_id = int(request.form['player2_id'])
        score1 = int(request.form['score1'])
        score2 = int(request.form['score2'])
        
        # Validate scores
        if player1_id != player2_id and isinstance(score1, int) and isinstance(score2, int):
            if (score1 == 5 or score2 == 5) and not (score1 == 5 and score2 == 5):
                # Update the score between player1 and player2
                if player1_id != player2_id:
                    win = score1 > score2
                    score = Score.query.filter_by(player1_id=player1_id, player2_id=player2_id).first()
                    if score:
                        score.score1 = score1
                        score.score2 = score2
                        score.win = win
                    else:
                        new_score = Score(player1_id=player1_id, player2_id=player2_id, score1=score1, score2=score2, win=win)
                        new_score_rev = Score(player1_id=player2_id, player2_id=player1_id, score1=score2, score2=score1, win=not win)
                        db.session.add(new_score)
                        db.session.add(new_score_rev)
                    db.session.commit()
                return redirect(url_for('index'))
        
        flash('Invalid score submission. One of the scores must be 5 and not both.')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
