import sys
import json
import functools

import pika

from postagemq.config import *
from postagemq.encoders import json_encoder as je
from postagemq import fingerprint as fp
from postagemq import exchange
from postagemq.messages import message as msg, results as res, commands as cmd
from postagemq.exceptions import TimeoutError


class GenericProducer(object):
    """A generic class that represents a message producer.
    This class enables the user to implement build_message_*()
    and build_rpc_*() methods and automatically provides the respective
    message_*() and rpc_*() methods that build the message with the
    given parameters, encodes and sends it.

    When a user calls producer.message_test() for example, the producer calls
    build_message_test() to create the message, then calls _message_send()
    to encode and send it

    Encoding can be changed giving the object a custom encoder object.
    The virtual host, the publishing exchange and the routing key can be
    customized with self.vhost, self.exchange and self.routing_key.

    The virtual host has some higher degree of cutomization: it can be
    specified when subclassing the object or when initializing it. The former
    is more appropriate for library objects which can be instanced by many
    components, while the latter is better suited for single instance objects
    or small environments.

    Message can be routed to different exchanges with different routing keys.
    When a message_*() method is called without passing a custom exchange or
    key the ones given as class attributes are used.
    When a message_*() method is called passing the routing key as the '_key'
    parameter the message is sent to the default exchange (the one given as
    class attribute) with that key.
    When a message_*() method is called passing a dictionary '_eks' of
    exchange/keys couples the exchange_class attribute has to be a dictionary
    of exchange names/exchange classses, and the names used sending the message
    shall be in this dictionary. If not the exchange is skipped.

    RPC messages are always sent to the 'default' exchange: that is either the
    only one you specified as class attribute or the one found with that key.
    """

    eks = [(exchange.Exchange, "nokey")]
    encoder_class = je.JsonEncoder

    # After this time the RPC call is considered failed
    rpc_timeout = 30

    # The RPC calls is repeated max_retry times
    max_retry = 4

    # Host, User, Password
    hup = global_hup

    def __init__(self, fingerprint=None, hup=None, vhost=None):
        if fingerprint is not None:
            _fingerprint = fingerprint
        else:
            _fingerprint = {}

        if hup is not None:
            self.hup = hup
        credentials = pika.PlainCredentials(self.hup['user'],
                                            self.hup['password'])
        host = self.hup['host']

        if vhost:
            self.vhost = vhost
        else:
            self.vhost = global_vhost

        conn_params = pika.ConnectionParameters(host, credentials=credentials,
                                                virtual_host=str(self.vhost))

        self.conn_broker = pika.BlockingConnection(conn_params)

        self.encoder = self.encoder_class()
        self.default_exchange = self.eks[0][0]
        self.fingerprint = fp.Fingerprint(name=sys.argv[0], vhost=self.vhost).as_dict()
        self.fingerprint.update(_fingerprint)

        self.channel = self.conn_broker.channel()
        if debug_mode:
            print("Producer {0} declaring eks {1}".
                  format(self.__class__.__name__, self.eks))
            print()
        for exc, key in self.eks:
            self.channel.exchange_declare(**exc.parameters)

    def _build_message_properties(self):
        msg_props = pika.BasicProperties()
        msg_props.content_type = self.encoder.content_type
        return msg_props

    def _build_rpc_properties(self):
        # Standard Pika RPC message properties
        msg_props = pika.BasicProperties()
        msg_props.content_type = self.encoder.content_type
        result = self.channel.queue_declare(exclusive=True, auto_delete=True)
        msg_props.reply_to = result.method.queue
        return msg_props

    def _encode(self, body):
        return json.dumps(body)

    def _get_eks(self, kwds):
        # Extracts a dictionary with Exchange/Key couples from kwds
        # Calling without keys returns self.eks
        # Calling with just _key=k returns [(default_exc, k)]
        # Calling with _key=k and _eks=ek_list returns ek_list
        # Calling with _eks=ek_list returns ek_list
        # where default_exc is the first exchange defined in self.eks
        # and ek_list is in the form
        # [(EXCHANGE, ROUTING_KEY), ...]
        #
        # This allows to call methods with just _key if the exchange is the
        # default one (or the only one) or with a complete EK specification.
        #
        # TODO: I do not like this way of passing values, I'd prefer to
        # leverage function atttributes and decorators. When there is
        # enough time...
        if '_key' in kwds:
            exchange = self.eks[0][0]
            return [(exchange, kwds.pop('_key'))]
        else:
            return kwds.pop('_eks', self.eks)

    def _message_send(self, *args, **kwds):
        eks = self._get_eks(kwds)
        msg_props = self._build_message_properties()

        # TODO: Why is this keyword not passed simply as named argument?
        callable_obj = kwds.pop('_callable')
        message = callable_obj(*args, **kwds)
        message.fingerprint(**self.fingerprint)
        encoded_body = self.encoder.encode(message.body)

        for exchange, key in eks:
            if debug_mode:
                print("--> {name}: basic_publish() to ({exc}, {key})".
                      format(name=self.__class__.__name__,
                             exc=exchange,
                             key=key))
                for _key, _value in message.body.items():
                    print("    {0}: {1}".format(_key, _value))
                print()
            self.channel.basic_publish(body=encoded_body,
                                       exchange=exchange.name,
                                       properties=msg_props,
                                       routing_key=key)

    def _rpc_send(self, *args, **kwds):
        eks = self._get_eks(kwds)
        timeout = kwds.pop('_timeout', self.rpc_timeout)
        max_retry = kwds.pop('_max_retry', self.max_retry)
        queue_only = kwds.pop('_queue_only', False)
        callable_obj = kwds.pop('_callable')

        message = callable_obj(*args, **kwds)
        message.fingerprint(**self.fingerprint)
        encoded_body = self.encoder.encode(message.body)

        exchange, key = eks[0]

        _counter = 0
        while True:
            try:
                # TODO: Message shall be sent again at each loop???
                msg_props = self._build_rpc_properties()
                if debug_mode:
                    print("--> {name}: basic_publish() to ({exc}, {key})".
                          format(name=self.__class__.__name__,
                                 exc=exchange,
                                 key=key))
                    for _key, _value in message.body.items():
                        print("    {0}: {1}".format(_key, _value))
                    print()
                self.channel.basic_publish(body=encoded_body,
                                           exchange=exchange.name,
                                           properties=msg_props,
                                           routing_key=key)

                if queue_only:
                    return msg_props.reply_to
                else:
                    results = self.consume_rpc(msg_props.reply_to,
                                               timeout=timeout)
                    return results[0]
            except TimeoutError as exc:
                if _counter < max_retry:
                    _counter = _counter + 1
                    continue
                else:
                    return res.MessageResultException(exc.__class__.__name__,
                                                      exc.__str__())

    def message(self, *args, **kwds):
        eks = self._get_eks(kwds)
        msg_props = self._build_message_properties()
        message = msg.Message(*args, **kwds)
        message.fingerprint(**self.fingerprint)
        encoded_body = self.encoder.encode(message.body)

        for exchange, key in eks:
            self.channel.basic_publish(body=encoded_body,
                                       exchange=exchange.name,
                                       properties=msg_props,
                                       routing_key=key)

    def forward(self, body, *args, **kwds):
        eks = self._get_eks(kwds)
        msg_props = self._build_message_properties()
        encoded_body = self.encoder.encode(body)

        for exchange, key in eks:
            self.channel.basic_publish(body=encoded_body,
                                       exchange=exchange.name,
                                       properties=msg_props,
                                       routing_key=key)

    def __getattr__(self, name):
        # This customization redirects message_*() and rpc_*() function calls
        # to _message_send() and _rpc_send() using respectively
        # build_message_*() and build_rpc_*() functions defined in
        # the subclass of this object.
        if name.startswith('message_'):
            command_name = name.replace('message_', '')
            func = 'build_message_' + command_name
            try:
                method = self.__getattribute__(func)
            except AttributeError:
                method = functools.partial(cmd.FFCommand, command_name)
            return functools.partial(self._message_send, _callable=method)
        elif name.startswith('rpc_'):
            command_name = name.replace('rpc_', '')
            func = 'build_rpc_' + command_name
            try:
                method = self.__getattribute__(func)
            except AttributeError:
                method = functools.partial(cmd.RPCCommand, command_name)
            return functools.partial(self._rpc_send, _callable=method)
        elif name.startswith('rpc_queue'):
            command_name = name.replace('rpc_queue_', '')
            func = 'build_rpc_' + command_name
            try:
                method = self.__getattribute__(func)
            except AttributeError:
                method = functools.partial(cmd.RPCCommand, command_name)
            return functools.partial(self._rpc_send,
                                     _callable=method,
                                     _queue_only=True)

    def consume_rpc(self, queue, result_len=1, callback=None, timeout=None):
        """Consumes an RPC reply.

        This function is used by a producer to consume a reply to an RPC call
        (thus the queue specified in the reply_to header must be specified
        as parameter.

        If a callback callable is given it is called after message has been
        received. The function returns the 'data' part of the reply message
        (a dictionary).
        """

        if timeout is None or timeout < 0:
            timeout = self.rpc_timeout

        result_list = []

        def _callback(channel, method, header, body):
            reply = self.encoder.decode(body.decode('UTF-8'))

            try:
                if reply['content']['type'] == 'success':
                    message = res.MessageResult(reply['content']['value'],
                                                reply['content']['message'])
                elif reply['content']['type'] == 'error':
                    message = res.MessageResultError(reply['content']['message'])
                elif reply['content']['type'] == 'exception':
                    message = res.MessageResultException(
                        reply['content']['value'],
                        reply['content']['message'])
                else:
                    raise ValueError
            except (KeyError, ValueError):
                message = res.MessageResultError("Malformed reply {0}".
                                                 format(reply['content']))

            result_list.append(message)
            if callback is not None:
                callback(reply)

            if len(result_list) == result_len:
                channel.stop_consuming()

        def _outoftime():
            self.channel.stop_consuming()
            raise TimeoutError

        tid = self.conn_broker.add_timeout(timeout, _outoftime)
        self.channel.basic_consume(_callback, queue=queue)
        self.channel.start_consuming()
        self.conn_broker.remove_timeout(tid)

        if len(result_list) == 0:
            result_list.append(res.MessageResultError('\
                An internal error occoured to RPC - result list was empty'))
        return result_list

    def serialize_text_file(self, filepath):
        with open(filepath, 'r') as f:
            result = {
                'name': os.path.basename(filepath),
                'content': f.readlines()
            }

        return result