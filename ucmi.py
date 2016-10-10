# doing execfile() on this file will alter the current interpreter's
# environment so you can import libraries in the virtualenv
#!/usr/bin/env python

import inspect , os
script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # script directory

activate_this_file = script_dir+ "/venv/bin/activate_this.py"

execfile(activate_this_file, dict(__file__=activate_this_file))



import math , json  , subprocess  , shutil

from flask import Flask , request, send_from_directory , session
from flask_login import login_user , UserMixin , LoginManager
from pythonScripts.send import sendMsg 


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


# deletes contents of static folder on startup
def init(folder = 'static/viewsheds'):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)
        
        
# Sets up folder for user
@app.route('/initUser', methods=['GET'])
def initUser():
    userid = returnID()
    userfolder = 'static/viewsheds/{0}'.format(userid)
    if os.path.exists(userfolder):
        init(userfolder)
    # viewsheds folder
    os.makedirs(userfolder + '/viewsheds')
    #dem folder
    os.makedirs(userfolder + '/dem')
    #done folder
    os.makedirs(userfolder + '/done')
    return '0'
    
    
def create_app(config_filename = None):
    app = Flask(__name__, static_url_path='')
    app.secret_key = 'xxxxyyyyyzzzzz'
    login_manager = LoginManager()
    login_manager.init_app(app)
    return app

def returnID():
    return str(request.remote_addr)


def deleteDoneFile(viewNum):
    doneFile = 'static/viewsheds/{0}/commonviewshed{1}.done'.format(returnID() , viewNum)
    if os.path.exists(doneFile):
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

# returns json item with location info
@app.route('/location', methods=['GET'])
def location():
    locationFile = 'viewshed1.json'
    locationDir = 'static/viewsheds/{0}/viewsheds/'.format(returnID())
    if os.path.isfile(locationDir+locationFile):
        return send_from_directory(locationDir, locationFile)
    else:
        return 'No location available'

# viewshed image
@app.route('/image/<viewNum>')
def image(viewNum):
    viewNum = int(viewNum)
    itemDir = 'static/viewsheds/{0}/'.format(returnID())
    locationFile = 'viewshed.png'
    if not os.path.isfile(itemDir+locationFile):
        return 'No image available'
    else:
        return send_from_directory(itemDir, locationFile)



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
@app.route('/isTaskDone/<dateStamp>' , methods=['GET'])
def isTaskDone(dateStamp):
    doneFile = script_dir + '/static/viewsheds/{0}/done/{1}.done'.format(returnID() , dateStamp)
    data = json.dumps({'done':os.path.exists(doneFile)})
    return data


# Checks if necessary elevation files are present and downloads if not available.
def srtmDownload(lat, lng):
    return -1 , -1


if __name__ == "__main__":
    print app.config
    init()
    app.run(debug=True)

    
    


