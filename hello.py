from flask import Flask , request, send_from_directory

from pythonScripts.viewsheds import grassViewshed

app = Flask(__name__, static_url_path='')

@app.route('/python', methods=['GET', 'POST'])
def pythonScript():
    lat = request.form['lat'];
    lng = request.form['lng'];
    grassViewshed(lat , lng)
    return lat , lng

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('js', path) #not sure why I have js directory, but it workds
    
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')
    


if __name__ == "__main__":
    app.run()
