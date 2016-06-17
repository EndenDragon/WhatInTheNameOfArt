from flask import Flask, render_template, jsonify, request
from config import *
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import *
import MySQLdb
import hmac
import hashlib
import subprocess
import os
import re
import json

app = Flask(__name__)
os.chdir(os.path.dirname(os.path.realpath(__file__)))

engine = create_engine('mysql://' + CONFIG_MYSQL_USERNAME + ':' + CONFIG_MYSQL_PASSWORD + '@' + CONFIG_MYSQL_IP + ':' + str(CONFIG_MYSQL_PORT) + '/' + CONFIG_MYSQL_DATABASE)
connection = engine.connect() #Connects to the mysql database

@app.route("/github-update", methods=["POST"]) #This is a github webhook. GitHub and ONLY github should visit the page, and they only do so via a POST request.
def github_update(): #This whole function happens after you hit that little push button on your git kraken :)
    h = hmac.new(CONFIG_GITHUB_WEBOOK_SECRET, request.data, hashlib.sha1) #Lets unhash whatever password github gave us with the password in our config
    if h.hexdigest() != request.headers.get("X-Hub-Signature", "")[5:]:  # A timing attack here is nearly impossible. // Then we compare if the passwords are equal
        return "FAIL" #If they are no equal, then return FAIL. else continue
    try:
        subprocess.Popen("git pull", shell=True).wait() #Run a command git pull that gets all the newest data
    except OSError: #If the server decideds to do something stupid with running the command, well we get an error
        return "ERROR"
    return "OK" #Otherwise, it should return OK

@app.route("/getGame/<id>") #Javascript should visit this page and get the mysql data. The ID will be passed in from the header of the browser/JS. And the ID will correspond with the row in the DB.
def storyline(id): #Now take in the ID in the definition
    query = """SELECT * FROM game WHERE id ='{0}'""".format(id) #gets the row with the ID in the database
    try:
        mysql = connection.execute(query) #Try and executes in the database
    except Exception as e: #If execution fails...
        connection = engine.connect() #Try and connect to mysql
        mysql = connection.execute(query) #Then Executes in the database again
    for x in mysql: #For each row returned from the database...
        gameState = str(x["gameState"]) #Set them in a variable
        players = str(x["players"])
        artist = str(x["artist"])
        winner = str(x["winner"])
        winner_id = str(x["winner_id"])
        word = str(x["word"])
        canvasData = str(x["canvasData"])
        guesses = str(x["guesses"])
    return jsonify(gameState=gameState, players=players, artist=artist, winner=winner, winner_id=winner_id, word=word, canvasData=canvasData, guesses=guesses)

@app.route("/updateGame/<idLoc>", methods=['POST'])
def updateGame(idLoc):
    column = str(request.form['column'])
    isJSONParam = str(request.form['isJSONParam']) == "True" or str(request.form['isJSONParam']) == "true"
    if isJSONParam:
        params = json.dumps(str(request.form['params']))
    else:
        params = str(request.form['params'])
    query = """UPDATE game SET """ + column + """='""" + params + """' WHERE id=""" + idLoc + """;"""
    try:
        mysql = connection.execute(query) #Try and executes in the database
    except Exception as e: #If execution fails...
        connection = engine.connect() #Try and connect to mysql
        mysql = connection.execute(query) #Then Executes in the database again
    return "OK"

@app.route("/")
def index():
    return render_template("index.html.jinja2")

@app.route("/newgame")
def newgame():
    return render_template("newgame.html.jinja2")

@app.route("/newlobby")
def newlobby():
    query = """SELECT COUNT(*) FROM game"""
    try:
        mysql = connection.execute(query) #Try and executes in the database
    except Exception as e: #If execution fails...
        connection = engine.connect() #Try and connect to mysql
        mysql = connection.execute(query) #Then Executes in the database again
    for x in mysql: #For each row returned from the database...
        t = str(x)
    t = re.sub('[^\d\.]', '', t)
    t = int(float(t)) + 1
    query = """INSERT INTO `game` (`id`, `gameState`, `players`, `artist`, `artist_id`, `winner`, `winner_id`, `word`, `canvasData`, `guesses`) VALUES (NULL, '0', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);"""
    try:
        mysql = connection.execute(query) #Try and executes in the database
    except Exception as e: #If execution fails...
        connection = engine.connect() #Try and connect to mysql
        mysql = connection.execute(query) #Then Executes in the database again
    return render_template("newlobby.html.jinja2", lobbyid=str(t))

@app.route("/projection/<idLoc>")
def projection(idLoc):
    return render_template("projection.html.jinja2", idLoc=idLoc)

@app.route("/projfinish/<idLoc>")
def projFinish(idLoc):
    return render_template("projfinish.html.jinja2", idLoc=idLoc)

@app.route("/join")
def join():
    return render_template("join.html.jinja2")

@app.route("/artistpanel/<idLoc>")
def artistpanel(idLoc):
    return render_template("artistpanel.html.jinja2", idLoc=idLoc)

if __name__ == "__main__":
    app.run(host=CONFIG_FLASK_IP,port=CONFIG_FLASK_PORT,debug=CONFIG_FLASK_DEBUGMODE)
