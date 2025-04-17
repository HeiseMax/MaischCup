from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import json

from helper import calculate_won_matches, calculate_lost_matches, calculate_remaining_matches, calculate_fraction_of_wins, calculate_total_points, calculate_total_points_received, calculate_point_difference, calculate_ranking

app = Flask(__name__)

app.secret_key = 'supersecretkey'  # Needed for flashing messages
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fencing.db' #'sqlite:///maisch2025_03.db'
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

@app.before_request
def set_default_session_values():
    if 'stats' not in session:
        session['stats'] = {
            "won": True,
            "lost": True,
            "remaining": True,
            "fraction": False,
            "points": False,
            "points_received": False,
            "index": False,
            "rank": False
        }

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle adding a new player
@app.route('/add_player', methods=['POST', 'GET'])
def add_player():
    if request.method == 'GET':
        return render_template('add_player.html')
    
    if request.method == 'POST':
        new_name = request.form['name']
        if Player.query.filter_by(name=new_name).first():
            session['player_id'] = Player.query.filter_by(name=new_name).first().id
            flash('Name schon eingetragen. Entweder du bist schon eingetragen, oder dein Namensvetter war schneller.')
        else:
            new_player = Player(name=new_name)
            db.session.add(new_player)
            db.session.commit()
            session['player_id'] = new_player.id
            return redirect(url_for('add_player'))
        return redirect(url_for('add_player'))

# Route to handle score updates
@app.route('/update_score', methods=['GET', 'POST'])
def update_score():
    if request.method == 'GET':
        players = Player.query.all()
        scores = Score.query.all()
        playersjson = json.dumps([{"id": player.id, "name": player.name} for player in players])
        scoresjson = json.dumps([{"player1_id": score.__dict__["player1_id"], "player2_id": score.__dict__["player2_id"]} for score in scores])
        return render_template('update_score.html', players=players, scores=scores, playersjson=playersjson, scoresjson=scoresjson)
    
    if request.method == 'POST':
        player1_id = int(request.form['player1_id'])
        player2_id = int(request.form['player2_id'])
        score1 = int(request.form['score1'])
        score2 = int(request.form['score2'])

        session['player_id'] = player1_id
        
        # Validate scores
        if player1_id != player2_id and isinstance(score1, int) and isinstance(score2, int):
            if (score1 == 5 or score2 == 5) and not (score1 == 5 and score2 == 5):
                # Update the score between player1 and player2
                if player1_id != player2_id:
                    win = score1 > score2
                    score = Score.query.filter_by(player1_id=player1_id, player2_id=player2_id).first()
                    score_rev = Score.query.filter_by(player1_id=player2_id, player2_id=player1_id).first()
                    if score:
                        score.score1 = score1
                        score.score2 = score2
                        score.win = win
                    if score_rev:
                        score_rev.score1 = score2
                        score_rev.score2 = score1
                        score_rev.win = not win
                    else:
                        new_score = Score(player1_id=player1_id, player2_id=player2_id, score1=score1, score2=score2, win=win)
                        new_score_rev = Score(player1_id=player2_id, player2_id=player1_id, score1=score2, score2=score1, win=not win)
                        db.session.add(new_score)
                        db.session.add(new_score_rev)
                    db.session.commit()
                return redirect(request.referrer)
        
        flash('Ergebnis nicht zulässig. Einer der beiden Punktestände muss 5 sein.')
        return redirect(request.referrer)
    
@app.route('/get_scores', methods=['GET'])
def get_scores():
    players = Player.query.all()
    scores = Score.query.all()
    won_matches = {player.id: calculate_won_matches(Score, player.id) for player in players}
    lost_matches = {player.id: calculate_lost_matches(Score, player.id) for player in players}
    remaining_matches = {player.id: calculate_remaining_matches(Score, Player, player.id) for player in players}
    win_fraction = {player.id: calculate_fraction_of_wins(Score, player.id) for player in players}
    points = {player.id: calculate_total_points(db, Score, player.id) for player in players}
    points_received = {player.id: calculate_total_points_received(db, Score, player.id) for player in players}
    point_difference = {player.id: calculate_point_difference(db, Score, player.id) for player in players}
    ranking = calculate_ranking(db, Player, Score)
    rank_mapping = {player["id"]: rank + 1 for rank, player in enumerate(ranking)}
    
    data = {
        "players": [{"id": player.id, "name": player.name} for player in players],
        "scores": [{"player1_id": score.player1_id, "player2_id": score.player2_id, "score1": score.score1, "score2": score.score2, "win": score.win} for score in scores],
        "stats" : [
            {"id": "won", "name": "Gewonnen", "value": won_matches, "show": False},
            {"id": "lost", "name": "Verloren", "value": lost_matches, "show": False},
            {"id": "remaining", "name": "Offen", "value": remaining_matches, "show": False},
            {"id": "fraction", "name": "Sieganteil", "value": win_fraction, "show": False},
            {"id": "points", "name": "Punkte", "value": points, "show": False},
            {"id": "points_received", "name": "Punkte erhalten", "value": points_received, "show": False},
            {"id": "index", "name": "Index", "value": point_difference, "show": False},
            {"id": "rank", "name": "Rang", "value": rank_mapping, "show": False}
        ]
    }
    for stat in data["stats"]:
        if session["stats"][stat["id"]]:
            stat["show"] = True

    return data
    
@app.route('/dev', methods=['GET', 'POST'])
def dev():
    if request.method == 'POST':
        # Update session stats based on form submission
        session['stats'] = {
            "won": 'won' in request.form,
            "lost": 'lost' in request.form,
            "remaining": 'remaining' in request.form,
            "fraction": 'fraction' in request.form,
            "points": 'points' in request.form,
            "points_received": 'points_received' in request.form,
            "index": 'index' in request.form,
            "rank": 'rank' in request.form,
        }
        return redirect(url_for('dev'))
    
    players = Player.query.all()
    scores = Score.query.all()
    stats=session['stats']
    return render_template('dev.html', players=players, scores=scores, stats=stats)
    
# Route to remove a player
@app.route('/remove_player/<int:player_id>', methods=['POST'])
def remove_player(player_id):
    player = Player.query.get(player_id)
    if player:
        # Remove all scores involving this player
        Score.query.filter((Score.player1_id == player_id) | (Score.player2_id == player_id)).delete()
        db.session.delete(player)
        db.session.commit()
        flash('Player removed successfully.')
    else:
        flash('Player not found.')
    return redirect(url_for('index'))

# Route to change a player's name
@app.route('/change_player_name/<int:player_id>', methods=['POST'])
def change_player_name(player_id):
    new_name = request.form['new_name']
    player = Player.query.get(player_id)
    if player:
        player.name = new_name
        db.session.commit()
        flash('Player name updated successfully.')
    else:
        flash('Player not found.')
    return redirect(url_for('index'))

# Route to remove a match
@app.route('/remove_match/<int:player1_id>/<int:player2_id>', methods=['POST'])
def remove_match(player1_id, player2_id):
    score = Score.query.filter_by(player1_id=player1_id, player2_id=player2_id).first()
    if score:
        db.session.delete(score)
        # Also remove the reverse match
        reverse_score = Score.query.filter_by(player1_id=player2_id, player2_id=player1_id).first()
        if reverse_score:
            db.session.delete(reverse_score)
        db.session.commit()
        flash('Match removed successfully.')
    else:
        flash('Match not found.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
