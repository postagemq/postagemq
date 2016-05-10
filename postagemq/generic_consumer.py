import collections

import pika

from postagemq.config import *
from postagemq.encoders import json_encoder as je
from postagemq.messages import results as res

class GenericConsumer(object):
    encoder_class = je.JsonEncoder
    vhost = global_vhost

    # Host, User, Password
    hup = global_hup

    # List of (Exchange, [(Queue, Key), (Queue, Key), ...])
    # Queue may be specified as string (the name of the queue) or
    # as a dictionary {'name':queue_name, 'flags':{'flag1':True,
    # 'flag2':False}}
    eqk = []

    def __init__(self, eqk=None, hup=None, vhost=None):
        if eqk is not None:
            _eqk = eqk
        else:
            _eqk = None

        if hup is not None:
            self.hup = hup
        credentials = pika.PlainCredentials(self.hup['user'],
                                            self.hup['password'])
        host = self.hup['host']

        if vhost:
            self.vhost = vhost
        conn_params = pika.ConnectionParameters(host, credentials=credentials,
                                                virtual_host=self.vhost)

        self.conn_broker = pika.BlockingConnection(conn_params)

        self.encoder = self.encoder_class()
        self.channel = self.conn_broker.channel()

        if len(_eqk) != 0:
            self.eqk = _eqk

        self.qk_list = []

        self.add_eqk(self.eqk)

        self.channel.basic_qos(prefetch_count=1)

        # Enabling this flag bypasses the msg_consumer function and just
        # rejects all messages
        self.discard_all_messages = False

    def add_eqk(self, eqk):
        for exchange_class, qk_list in eqk:
            for queue_info, key in qk_list:
                if isinstance(queue_info, collections.Mapping):
                    self.queue_bind(exchange_class,
                                    queue_info['name'],
                                    key,
                                    **queue_info['flags'])
                else:
                    self.queue_bind(exchange_class, queue_info, key)

    def queue_bind(self, exchange_class, queue, key, **kwds):
        if debug_mode:
            print("Consumer {name}: Declaring exchange {e}".
                  format(name=self.__class__.__name__,
                         e=exchange_class))
        self.channel.exchange_declare(**exchange_class.parameters)

        if debug_mode:
            print("Consumer {name}: Declaring queue {q}".
                  format(name=self.__class__.__name__,
                         q=queue))
        self.channel.queue_declare(queue=queue, **kwds)

        if debug_mode:
            print("Consumer {name}: binding queue {q} with exchange {e} with routing key {k}".
                  format(name=self.__class__.__name__,
                         q=queue,
                         e=exchange_class,
                         k=key))
        self.channel.queue_bind(queue=queue, exchange=exchange_class.name,
                                routing_key=key)
        self.qk_list.append((queue, key))

    def queue_unbind(self, exchange_class, queue, key):
        self.channel.exchange_declare(**exchange_class.parameters)
        self.channel.queue_unbind(queue=queue, exchange=exchange_class.name,
                                  routing_key=key)

    def start_consuming(self, callback):
        for queue, key in self.qk_list:
            self.channel.basic_consume(callback, queue=queue)
        self.channel.start_consuming()

    def stop_consuming(self):
        self.channel.stop_consuming()

    def ack(self, method):
        self.channel.basic_ack(delivery_tag=method.delivery_tag)

    def reject(self, method, requeue):
        self.channel.basic_reject(delivery_tag=method.delivery_tag,
                                  requeue=requeue)

    def decode(self, data):
        return self.encoder.decode(data)

    def rpc_reply(self, header, message):
        try:
            encoded_body = self.encoder.encode(message.body)
        except AttributeError:
            msg = res.MessageResult(message)
            encoded_body = self.encoder.encode(msg.body)

        self.channel.basic_publish(body=encoded_body, exchange="",
                                   routing_key=header.reply_to)


