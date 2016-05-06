from postagemq.messages import message as msg


class MessageResult(msg.Message):
    """Result of an RPC call.
    This type of message adds the follwing keys to the message content: type
    (the type of result - success, error of exception), value (the Python value
    for the result) and message (another good naming choice: a string
    describing the result).
    Results can be of three type: success represents a successful call, error
    represents something that can be forecasted when the code of the call has
    been written, and shall be documented, while exception is a Python
    which happened in the remote executor. This error classification has been
    inspired by Erlang error management, which I find a good solution.
    """
    type = 'result'
    result_type = 'success'

    def __init__(self, value, message=''):
        super(MessageResult, self).__init__()
        self.body['content']['type'] = self.result_type
        self.body['content']['value'] = value
        self.body['content']['message'] = message


class MessageResultError(MessageResult):
    type = 'result'
    result_type = 'error'
    boolean_value = False

    def __init__(self, message):
        super(MessageResultError, self).__init__(None, message)


class MessageResultException(MessageResult):
    type = 'result'
    result_type = 'exception'
    boolean_value = False

    def __init__(self, name, message):
        super(MessageResultException, self).__init__(name, message)
