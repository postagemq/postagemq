import sys
import traceback
import copy
import functools

import six

from postagemq import handlers as hdl
from postagemq import microthreads
from postagemq.config import *
from postagemq import exceptions as ex
from postagemq import generic_consumer as gc
from postagemq.messages import results as res


class MessageProcessor(six.with_metaclass(hdl.MessageHandlerType, microthreads.MicroThread)):
    """A MessageProcessor is a MicroThread with MessageHandlerType as
    metaclass. This means that it can be used as a microthred in a scheduler
    and its methods can be decorated with the MessageHandler decorator.
    Two standard message handler are available ('command', 'quit') and
    ('command', 'restart'). The _msg_consumer() method loops over message
    handlers to process each incoming message.
    """

    consumer_class = gc.GenericConsumer

    def __init__(self, fingerprint, eqk, hup, vhost):
        # This is a generic consumer, customize the consumer_class class
        # attribute with your consumer of choice
        self.consumer = self.consumer_class(eqk, hup, vhost)
        self.fingerprint = fingerprint

    def add_eqk(self, eqk):
        self.consumer.add_eqk(eqk)

    def add_timeout(self, seconds, callback=None):
        if callback is not None:
            self.consumer.conn_broker.add_timeout(seconds, callback)
        else:
            self.consumer.conn_broker.sleep(seconds)

    @hdl.MessageHandler('command', 'quit')
    def msg_quit(self, content):
        self.consumer.stop_consuming()
        raise microthreads.ExitScheduler

    @hdl.MessageHandler('command', 'restart')
    def msg_restart(self, content):
        self.consumer.stop_consuming()
        raise ex.AckAndRestart

    def restart(self):
        executable = sys.executable
        os.execl(executable, executable, *sys.argv)

    def _filter_message(self, callable_obj, message_body):
        filtered_body = {}
        filtered_body.update(message_body)

        try:
            for _filter, args, kwds in callable_obj.filters:
                try:
                    filtered_body = _filter(filtered_body, *args, **kwds)
                except ex.FilterError as exc:
                    if debug_mode:
                        print("Filter failure")
                        print("  Filter:", _filter)
                        print("  Args:  ", args)
                        print("  Kwds:  ", kwds)
                        print("  Filter message:", exc.args)
                    raise
        except AttributeError:
            pass

        return filtered_body

    def _msg_consumer(self, channel, method, header, body):
        decoded_body = self.consumer.decode(body.decode('UTF-8'))

        if debug_mode:
            print("<-- {0}: _msg_consumer()".format(self.__class__.__name__))
            for _key, _value in decoded_body.items():
                print("    {0}: {1}".format(_key, _value))
            print()
        try:
            message_category = decoded_body['category']
            message_type = decoded_body['type']
            if message_category == "message":
                message_name = decoded_body['name']

                handlers = self._message_handlers.get((message_category,
                                                       message_type,
                                                       message_name), [])

                for callable_obj, body_key in handlers:
                    # Copies are made to avoid filters change the original
                    # message that could be parsed by other handlers
                    if body_key is None:
                        filtered_body = copy.deepcopy(decoded_body)
                    else:
                        filtered_body = copy.deepcopy(decoded_body[body_key])

                    try:
                        filtered_body = self._filter_message(
                            callable_obj, filtered_body)

                        callable_obj(self, filtered_body)
                    except ex.FilterError:
                        if debug_mode:
                            print("Filter error in handler", callable_obj)
            elif message_category == 'rpc':
                reply_func = functools.partial(
                    self.consumer.rpc_reply, header)

                try:

                    if message_type == 'command':
                        message_name = decoded_body['name']

                        handlers = self._message_handlers.get((message_category,
                                                               message_type,
                                                               message_name), [])

                        if len(handlers) != 0:
                            callable_obj, body_key = handlers[-1]
                            filtered_body = {}
                            filtered_body.update(decoded_body['content'])

                            try:
                                filtered_body = self._filter_message(
                                    callable_obj, filtered_body)
                                callable_obj(self, filtered_body, reply_func)
                            except ex.FilterError:
                                if debug_mode:
                                    print(
                                        "Filter error in handler", callable_obj)
                except Exception as exc:
                    reply_func(res.MessageResultException(
                        exc.__class__.__name__, exc.__str__()))
                    raise

            # Ack it since it has been processed - even if no handler
            # recognized it
            self.consumer.ack(method)

        except (microthreads.ExitScheduler, StopIteration):
            self.consumer.ack(method)
            raise
        except ex.RejectMessage:
            self.consumer.reject(method, requeue=False)
        except ex.AckAndRestart:
            self.consumer.ack(method)
            self.restart()
        except Exception as exc:
            print("Unmanaged exception in {0}".format(self))
            print(exc)
            traceback.print_exc()
            self.consumer.reject(method, requeue=False)

        return

    def start_consuming(self):
        self.consumer.start_consuming(callback=self._msg_consumer)

    def stop_consuming(self):
        self.consumer.stop_consuming()

    def step(self):
        self.start_consuming()
