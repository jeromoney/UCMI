import math

from flask import Flask , request, send_from_directory
from pythonScripts.viewsheds64 import grassViewshed , grassCommonViewpoints
from pythonScripts.srtmsql64 import pointQuery

app = Flask(__name__, static_url_path='')

@app.route('/elevationfilter', methods=['GET', 'POST'])
def elevationfilter():
    form = request.form
    altitude = float(form['altitude'])
    greaterthan = (form['greaterthan'] == 'greaterthan')
    viewNum = int(form['viewNum'])
    grassCommonViewpoints(viewNum , greaterthan , altitude)
    return '0'

@app.route('/python', methods=['GET', 'POST'])
def pythonScript():
    form = request.form
    altitude = float(form['altitude'])
    lat = form['lat']
    lng = form['lng']
    pointNum = int(form['size'])
    viewNum = int(form['viewNum'])
    firstMarker = (pointNum == 1)
    greaterthan = (form['greaterthan'] == 'greaterthan')
    pointQuery(lat , lng , pointNum, firstMarker , viewNum , greaterthan , altitude)
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
    app.run(debug=True)
