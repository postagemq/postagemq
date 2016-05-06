import six
from postagemq.messages import message as msg


class FFCommand(msg.Message):
    """The base implementation of a command message.
    """
    type = 'command'

    def __init__(self, command, parameters=None):
        if parameters is not None:
            _parameters = parameters
        else:
            _parameters = {}

        if six.PY2:
            super(FFCommand, self).__init__()
        else:
            super().__init__()
        self.body['name'] = str(command)
        self.body['content']['parameters'] = _parameters


class RPCCommand(FFCommand):
    """The base implementation of an RPC message.
    This is exactly the same as a standard cammand message. This is implemented
    in a custom class to allow us to tell apart which messages need an answer.
    """
    type = 'command'
    category = 'rpc'
