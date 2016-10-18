#!/usr/bin/env python
'''
RabbitMQ receiver. Jobs are retreived as messages and converted into
python calls.
'''
activate_this_file = "../venv/bin/activate_this.py"
execfile(activate_this_file, dict(__file__=activate_this_file))

from viewsheds import grassCommonViewpoints
from srtmsql import pointQuery , makeTransparent
import pika , json , configparser


config = configparser.ConfigParser()
config.read('../config.ini')
options_ucmi = config._sections['ucmi.py']
viewshedDir = '../' + options_ucmi['viewsheddir'] 


# Connecting to RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()
channel.queue_delete(queue='task_queue')
channel.queue_declare(queue='task_queue')

def callback(ch, method, properties, body):
    form = json.loads(body)[1]
    fnction = json.loads(body)[0]
    id = json.loads(body)[2]
    altitude = float(form['altitude'])
    greaterthan = (form['greaterthan'] == 'greaterthan')
    viewNum = int(form['viewNum'])
    dateStamp = form['dateStamp']
    if fnction == 'grassCommonViewpoints':
        grassCommonViewpoints(viewNum , greaterthan , altitude , id , dateStamp)
        makeTransparent(id)
    elif fnction == 'pointQuery':
        lat = form['lat']
        lng = form['lng']
        pointNum = int(form['size'])
        firstMarker = (pointNum == 1)
        pointQuery(lat , lng , pointNum, firstMarker , viewNum , greaterthan , altitude , id , dateStamp)
    
    # Process is completed, create empty done file
    print(" [x] Done:  %r" % body)
    f = file('/'.join([viewshedDir , id , dateStamp + '.done']), 'w')
    f.close()


channel.basic_consume(callback,
                      queue='task_queue')

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
