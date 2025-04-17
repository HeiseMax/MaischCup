# Function to calculate won matches
def calculate_won_matches(Score, player_id):
    return Score.query.filter_by(player1_id=player_id, win=True).count()

# Function to calculate lost matches
def calculate_lost_matches(Score, player_id):
    return Score.query.filter_by(player1_id=player_id, win=False).count()

# Function to calculate remaining matches
def calculate_remaining_matches(Score, Player, player_id):
    return Player.query.count() - 1 - Score.query.filter_by(player1_id=player_id).count()

# Function to calculate the fraction of wins
def calculate_fraction_of_wins(Score, player_id):
    total_matches = Score.query.filter((Score.player1_id == player_id) | (Score.player2_id == player_id)).count()
    if total_matches == 0:
        return 0  # Avoid division by zero
    won_matches = Score.query.filter_by(player1_id=player_id, win=True).count()
    return won_matches / total_matches

# Function to calculate total points scored by a player
def calculate_total_points(db, Score, player_id):
    points_as_player1 = db.session.query(db.func.sum(Score.score1)).filter(Score.player1_id == player_id).scalar() or 0
    points_as_player2 = db.session.query(db.func.sum(Score.score2)).filter(Score.player2_id == player_id).scalar() or 0
    return points_as_player1 + points_as_player2

# Function to calculate total points received by a player
def calculate_total_points_received(db, Score, player_id):
    points_received_as_player1 = db.session.query(db.func.sum(Score.score2)).filter(Score.player1_id == player_id).scalar() or 0
    points_received_as_player2 = db.session.query(db.func.sum(Score.score1)).filter(Score.player2_id == player_id).scalar() or 0
    return points_received_as_player1 + points_received_as_player2

# Function to calculate the point difference for a player
def calculate_point_difference(db, Score, player_id):
    total_points = calculate_total_points(db, Score, player_id)
    total_points_received = calculate_total_points_received(db, Score, player_id)
    return total_points - total_points_received

# Function to calculate the ranking of players
def calculate_ranking(db, Player, Score):
    players = Player.query.all()
    ranking = []

    for player in players:
        player_data = {
            "id": player.id,
            "name": player.name,
            "wins": calculate_won_matches(Score, player.id),
            "point_difference": calculate_point_difference(db, Score, player.id),
        }
        ranking.append(player_data)

    # Sort by number of wins (descending) and then by point difference (descending)
    ranking.sort(key=lambda x: (x["wins"], x["point_difference"]), reverse=True)

    return ranking
