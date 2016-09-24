from flask import Flask , request, send_from_directory

app = Flask(__name__, static_url_path='')

@app.route('/python')
def pythonScript():
    return 'dick butt'

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('js', path)
    
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')
    


if __name__ == "__main__":
    app.run()
