# doing execfile() on this file will alter the current interpreter's
# environment so you can import libraries in the virtualenv
#!/usr/bin/env python
activate_this_file = "venv/bin/activate_this.py"

execfile(activate_this_file, dict(__file__=activate_this_file))

import math , json , os

from flask import Flask , request, send_from_directory , session
from flask_login import login_user , UserMixin , LoginManager
from pythonScripts.send import sendMsg 
# TODO: Start msg server script in seperate process

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

def deleteDoneFile(viewNum):
    doneFile = 'static/viewsheds/{0}/commonviewshed{1}.done'.format(returnID() , viewNum)
    os.remove(doneFile)

@app.route('/elevationfilter', methods=['GET', 'POST'])
def elevationfilter():
    deleteDoneFile(request.form['viewNum'])
    formStr = json.dumps(['grassCommonViewpoints'] + [request.form] + [returnID()])
    sendMsg(formStr)
    return '0'

@app.route('/python', methods=['GET', 'POST'])
def pythonScript():
    deleteDoneFile(request.form['viewNum'])
    formStr = json.dumps(['pointQuery'] + [request.form] + [returnID()])
    sendMsg(formStr)
    return '0'

# user specific itmes
@app.route('/viewsheds/<filename>')
def serve_usrstatic(filename):
    itemDir = 'static' + '/viewsheds/' + str(returnID())
    return send_from_directory(itemDir, filename)

# user non-specific items
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('js', path) #not sure why I have js directory, but it works

@app.route('/')
def index():
    user = User()
    login_user(user, remember=True)
    return send_from_directory('static', 'index.html')

# checks if task is done
@app.route('/isTaskDone/<viewNum>' , methods=['GET'])
def isTaskDone(viewNum):
    doneFile = 'static/viewsheds/{0}/commonviewshed{1}.done'.format(returnID() , viewNum)
    return str(os.path.exists(doneFile))


# Checks if necessary elevation files are present and downloads if not available.
def srtmDownload(lat, lng):
    return -1 , -1


if __name__ == "__main__":
    print app.config
    app.run(debug=True)
