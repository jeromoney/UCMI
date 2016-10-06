#!/usr/bin/env python


import pika

def sendMsg(formStr):

    connection = pika.BlockingConnection(pika.ConnectionParameters(
                   'localhost'))
    channel = connection.channel()


    channel.queue_declare(queue='hello')
    channel.basic_publish(exchange='',
                          routing_key='hello',
                          body= formStr)
                          
                          
                      
#print(" [x] Sent 'Hello World!'")
