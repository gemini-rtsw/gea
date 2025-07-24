#!/usr/bin/env python3
import pika
import json
import sys

def sendRabbitMsg(msg):
    """
       Send a generic rabbit message.
    """

    cred = pika.PlainCredentials('gea', 'gea')
    con  = pika.BlockingConnection( pika.ConnectionParameters('localhost', 5672, '/', cred))
    ch   = con.channel()

    msg  = json.dumps(msg)

    ch.exchange_declare(exchange='sysmon', exchange_type='fanout')
    ch.basic_publish(exchange='sysmon', routing_key='', body = msg)

    con.close()

if __name__ == '__main__':
  sendRabbitMsg({"type":"email", "system":"ALTAIR", "email":"on"})
  # sendRabbitMsg({"type":"email", "system":"ECS", "email":"on"})
  # sendRabbitMsg({"type":"email", "system":"GMOS", "email":"on"})
  # sendRabbitMsg({"type":"email", "system":"GNIRS", "email":"on"})
  # sendRabbitMsg({"type":"email", "system":"NIFS", "email":"on"})
  # sendRabbitMsg({"type":"email", "system":"NIRI", "email":"on"})
  # sendRabbitMsg({"type":"email", "system":"PR1", "email":"on"})
  # sendRabbitMsg({"type":"email", "system":"PR2", "email":"on"})
  # sendRabbitMsg({"type":"email", "system":"PR4", "email":"on"})
  # sendRabbitMsg({"type":"email", "system":"SCS", "email":"on"})
