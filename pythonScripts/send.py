#!/usr/bin/env python


import pika

def sendMsg(formStr):

    connection = pika.BlockingConnection(pika.ConnectionParameters(
                   'localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue')
    channel.basic_publish(exchange='',
                      routing_key='task_queue',
                      body=formStr,
                      )
    connection.close()
