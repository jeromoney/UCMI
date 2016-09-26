import math

from flask import Flask , request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from pythonScripts.viewsheds import grassViewshed

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username

app = Flask(__name__, static_url_path='')
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://justin:bobo24@localhost/myDB"
db = SQLAlchemy(app)
print db


@app.route('/python', methods=['GET', 'POST'])
def pythonScript():
    lat = request.form['lat']
    lng = request.form['lng']
    region , srtm_files = srtmDownload(lat, lng)
    
    grassViewshed(lat , lng)
    return lat , lng

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('js', path) #not sure why I have js directory, but it workds
    
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')
    

# Checks if necessary elevation files are present and downloads if not available.
def srtmDownload(lat, lng):
    
    return -1 , -1


if __name__ == "__main__":
    print app.config
    app.run()
