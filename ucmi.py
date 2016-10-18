#!/usr/bin/env python
'''
ucmi.py
Configures flask server and routes web requests to appropiate python
 scripts. Scripts aren't called directly, but instead sent as a message
 to a RabbitMQ server.
'''

# Importing settings
import configparser , inspect , os
config = configparser.ConfigParser()
config.read('config.ini')
this_file = inspect.getfile(inspect.currentframe())
options = config._sections[this_file]

# Setting up virtual python environment
# the current script directory 
script_dir = os.path.dirname(os.path.abspath(this_file)) 
activate_this_file = script_dir + options['venv']
execfile(activate_this_file, dict(__file__=activate_this_file))

import math , json , subprocess , shutil

from flask import Flask , request, send_from_directory , session
from pythonScripts.send import sendMsg 

        
app = Flask(__name__, static_url_path='')
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)


# deletes contents of static folder on startup
def init(folder = options['viewsheddir']):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)
        
        
# sets up personal folder for user
def initUser():
    userid = returnID()
    userfolder = script_dir + '/' + options['viewsheddir'] + userid
    print userfolder
    if os.path.exists(userfolder):
        init(script_dir + userfolder)
    demFolder = userfolder + '/' + options['demdir']
    print demFolder
    if not os.path.exists(demFolder):
        os.makedirs(demFolder)
    return '0'
    
    
def create_app(config_filename = None):
    app = Flask(__name__, static_url_path='')
    login_manager = LoginManager()
    login_manager.init_app(app)
    return app

# IP is used as user id. This could be done better
def returnID():
    return str(request.remote_addr)

# User has requested area to be filtered by elevation alone
@app.route('/elevationfilter', methods=['GET', 'POST'])
def elevationfilter():
    formStr = json.dumps(['grassCommonViewpoints'] + [request.form] + [returnID()])
    sendMsg(formStr)
    return '0'

# Main call. User has submitted a viewshed and possibly elevation filter
# request.
@app.route('/python', methods=['GET', 'POST'])
def pythonScript():
    #if this is the first request, set up user folder
    if request.form['viewNum'] == '0':
        initUser()
    formStr = json.dumps(['pointQuery'] + [request.form] + [returnID()])
    sendMsg(formStr)
    return '0'

# returns json item with location info
@app.route('/location', methods=['GET'])
def location():
    locationFile = options['locationjson']
    locationDir = options['viewsheddir'] + returnID() + '/'
    if os.path.isfile(locationDir+locationFile):
        return send_from_directory(locationDir, locationFile)
    else:
        return 'No location available'

# returns the viewshed image
@app.route('/image')
def image():
    locationDir = options['viewsheddir'] + returnID() + '/'
    locationFile = options['locationpng']
    if not os.path.isfile(locationDir+locationFile):
        return 'No image available'
    else:
        return send_from_directory(locationDir, locationFile)

# user specific itmes
@app.route('/viewsheds/<filename>')
def serve_usrstatic(filename):
    try:
        assert(False)
    except:
        print('This function should not have been used.')
        assert(False)
    itemDir = 'static' + '/viewsheds/' + str(returnID())
    return send_from_directory(itemDir, filename)

# user non-specific items
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('js', path) #not sure why I have js directory, but it works


# checks if task is done
@app.route('/isTaskDone/<dateStamp>' , methods=['GET'])
def isTaskDone(dateStamp):
    doneFile = script_dir + '/' + options['viewsheddir'] + returnID() + '/' + dateStamp + '.done'
    print doneFile
    data = json.dumps({'done':os.path.exists(doneFile)})
    return data

# Routes incoming requests to main index file.
@app.route('/')
def index():
    return send_from_directory(options['staticdir'], 'index.html')

if __name__ == "__main__":
    print app.config
    init()
    app.run(debug= config.getboolean(this_file, "debug"))

    
    


