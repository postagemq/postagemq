import six


class MessageHandler(object):
    """This decorator takes two parameters: message_type and message_name.
    message_type is the type of message the handler can process
    (e.g. "command", "status") message_name is the actual message name
    Decorating a method with this class marks it so that it is called every
    time a message with that type and name is received.
    """

    def __init__(self, message_type, message_name=None):
        self.handler_data = ("message", message_type, message_name, 'content')

    def __call__(self, func):
        func._message_handler = self.handler_data
        return func


class RpcHandler(MessageHandler):
    """This decorator takes two parameters: message_type and message_name.
    message_type is the type of message the handler can process
    (e.g. "command", "status") message_name is the actual message name
    Decorating a method with this class marks it so that it is called every
    time an RPC with that type and name is received.
    """

    def __init__(self, message_type, message_name=None):
        self.handler_data = ("rpc", message_type, message_name, 'content')


class MessageHandlerFullBody(MessageHandler):
    """This decorator behaves the same as MessageHandler but makes the
    decorated method receive the full message body instead the sole content.
    """

    def __init__(self, handler_type, message_name=None):
        self.handler_data = ("message", handler_type, message_name, None)


class MessageFilter(object):
    """This decorator takes as parameter a callable. The callable must accept
    a message as argument and is executed every time a message is processed
    by the decorated function.

    The callable shall return the filtered message. Any exception will result
    in the message being discarded without passing through the message handler.

    Example:

    def filter_message(message):
        [...]

    @messaging.MessageFilter(filter_message)
    @messaging.MessageHandler('command', 'a_command')
    def a_command(self, content):
        [...]

    When a message is processed by a_command() it is first processed by
    filter_message().

    """

    def __init__(self, _callable, *args, **kwds):
        self.callable = _callable
        self.args = args
        self.kwds = kwds

    def __call__(self, func):
        try:
            func.filters.append((self.callable, self.args, self.kwds))
        except AttributeError:
            func.filters = [(self.callable, self.args, self.kwds)]
        return func


class MessageHandlerType(type):
    """This metaclass is used in conjunction with the MessageHandler decorator.
    An object with this metaclass has an internal dictionary called
    _message_handlers that contains all methods which can process an incoming
    message keyed by message type. The dictionary is filled by the __init__ of
    the metaclass, looking for the attribute _message_handler attached by the
    MessageHandler decorator.
    """

    def __init__(self, name, bases, attrs):
        if six.PY2:
            super(MessageHandlerType, self).__init__(name, bases, attrs)
        else:
            super().__init__(name, bases, attrs)

        try:
            self._message_handlers
        except AttributeError:
            self._message_handlers = {}

        for key, method in attrs.items():
            if hasattr(method, '_message_handler'):
                message_category, message_type, message_name, body_key = \
                    method._message_handler

                message_key = (message_category, message_type, message_name)

                if message_key not in self._message_handlers:
                    self._message_handlers[message_key] = []

                self._message_handlers[message_key].append((method, body_key))
