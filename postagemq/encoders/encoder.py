class Encoder(object):
    """The base message encoder.
    An encoder knows how to encode and decode messages
    to plain strings which can be delivered by AMQP.
    """

    content_type = ""

    @classmethod
    def encode(cls, data):
        """Encodes data to a plain string.

        :param data: a Python object
        :type data: object

        """
        return data

    @classmethod
    def decode(cls, string):
        """Decodes data from a plain string.

        :param string: a plain string previously encoded
        """

        return string
