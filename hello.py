import math

from flask import Flask , request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from pythonScripts.viewsheds import grassViewshed
from pythonScripts.srtmsql import pointQuery

app = Flask(__name__, static_url_path='')


@app.route('/python', methods=['GET', 'POST'])
def pythonScript():
    lat = request.form['lat']
    lng = request.form['lng']
    pointNum = int(request.form['size'])
    viewNum = int(request.form['viewNum'])
    firstMarker = (pointNum == 1)
    pointQuery(lat, lng , pointNum, firstMarker , viewNum)
    return '0'

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
