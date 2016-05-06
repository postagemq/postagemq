import six


class Message(object):
    """This class is the base Postage message.
    Message type can be 'command', 'status' or 'result'. Command messages
    transport a command we want to send to a component, either a direct one or
    an RPC one. Status messages transport the status of an application. Result
    messages transport the result of an RPC.
    Message category tells simple commands ('message') from RPC ('rpc'). The
    nomenclature is a little confusing, due to historical reasons (the standard
    excuse to cover bad choices).
    A message has also a boolean representation, through boolean_value.
    The payload of a message can be found inside the 'content' key of the
    message 'body' attribute.
    """
    type = 'none'
    name = 'none'
    category = 'message'
    boolean_value = True

    def __init__(self, *args, **kwds):
        self.body = {
            'type': self.type,
            'name': self.name,
            'category': self.category,
            'version': '2',
            'fingerprint': {},
            'content': {}
        }

        if len(args) != 0:
            self.body['content']['args'] = args
        if len(kwds) != 0:
            self.body['content']['kwds'] = kwds
        self.body['_reserved'] = {}

    if six.PY2:
        def __unicode__(self):
            return unicode(self.body)

    def __str__(self):
        if six.PY2:
            return unicode(self.body).encode('utf-8')
        else:
            return str(self.body)

    def __eq__(self, msg):
        return self.body == msg.body

    def __nonzero__(self):
        return self.boolean_value

    def fingerprint(self, **kwds):
        self.body['fingerprint'].update(kwds)


class MessageStatus(Message):
    """Status of a component.
    A component which wants to send its status to another component
    can leverage this type of message. It adds to the content the
    key name (the name of the message, which is the status itself)
    and application, which is another dictionary containing the following
    information on the component: name, type, pid, host, user, vhost. These six
    values are the standard values a component carries around. Here type has
    nothing to do with messages, but represents a classification of the
    component sending the status.
    """
    type = 'status'

    def __init__(self, status):
        super(MessageStatus, self).__init__()
        self.body['name'] = str(status)
