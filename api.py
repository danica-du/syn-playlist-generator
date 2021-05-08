from flask import Flask, request, render_template,jsonify
app = Flask(__name__)
import playlist_generator as pg
import random

def do_something(word):
    ans = []
    for i in range(10):
        ans.append(word + str(i))
    return ans

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/playlist', methods=['GET','POST'])
def show_playlist():
    if request.method == "POST":
        keyword = request.form["keyword"]
        numsongs = request.form["numsongs"]
        print(numsongs)
        syns = pg.get_synonyms(keyword)  # list of synonyms
        playlist = pg.get_playlist(syns, numsongs)

        return render_template("showplaylist.html", val=playlist)

if __name__ == '__main__':
    app.run(debug=True)