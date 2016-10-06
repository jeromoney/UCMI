#!/usr/bin/env python
activate_this_file = "../venv/bin/activate_this.py"
execfile(activate_this_file, dict(__file__=activate_this_file))

from viewsheds64 import grassCommonViewpoints
from srtmsql64 import pointQuery


import pika , json

connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='hello')

def callback(ch, method, properties, body):
    form = json.loads(body)[1]
    fnction = json.loads(body)[0]
    id = json.loads(body)[2]
    altitude = float(form['altitude'])
    greaterthan = (form['greaterthan'] == 'greaterthan')
    viewNum = int(form['viewNum'])
    if fnction == 'grassCommonViewpoints':
        grassCommonViewpoints(viewNum , greaterthan , altitude , id)
    elif fnction == 'pointQuery':
        lat = form['lat']
        lng = form['lng']
        pointNum = int(form['size'])
        firstMarker = (pointNum == 1)
        pointQuery(lat , lng , pointNum, firstMarker , viewNum , greaterthan , altitude , id)
    
    

    print(" [x] Received %r" % body)

channel.basic_consume(callback,
                      queue='hello',
                      no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
