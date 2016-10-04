import math

from flask import Flask , request, send_from_directory , session
from flask.ext.login import login_user , UserMixin , LoginManager
from pythonScripts.viewsheds64 import grassCommonViewpoints
from pythonScripts.srtmsql64 import pointQuery

class User(UserMixin):
    def __init__(self):
        self.id = ''
    @classmethod
    def get(cls,id):
        return cls.user_database.get(id)

        
        
app = Flask(__name__, static_url_path='')
app.secret_key = 'xxxxyyyyyzzzzz'
login_manager = LoginManager()
login_manager.init_app(app)

def returnID():
    userid = request.cookies.get('remember_token')
    if userid is None:
        userid = max(request.cookies.get('session') , 'anonymous')
    userid = userid[-9:]
    return userid


@app.route('/elevationfilter', methods=['GET', 'POST'])
def elevationfilter():
    form = request.form
    altitude = float(form['altitude'])
    greaterthan = (form['greaterthan'] == 'greaterthan')
    viewNum = int(form['viewNum'])
    grassCommonViewpoints(viewNum , greaterthan , altitude , returnID())
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
    pointQuery(lat , lng , pointNum, firstMarker , viewNum , greaterthan , altitude , returnID())
    return '0'

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('js', path) #not sure why I have js directory, but it works
    
@app.route('/')
def index():
    user = User()
    login_user(user, remember=True)
    return send_from_directory('static', 'index.html')
    

# Checks if necessary elevation files are present and downloads if not available.
def srtmDownload(lat, lng):
    return -1 , -1


if __name__ == "__main__":
    print app.config
    app.run(debug=True)
