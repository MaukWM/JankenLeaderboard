import json

from flask import Flask, jsonify, render_template

app = Flask(__name__)

# Sample JSON data
with open("../leaderboard.json", "r") as json_file:
    leaderboard_data = json.load(json_file)

@app.route('/leaderboard')
def get_leaderboard():
    return render_template('index.html', leaderboard_data=leaderboard_data)


if __name__ == '__main__':
    app.run(debug=True)
