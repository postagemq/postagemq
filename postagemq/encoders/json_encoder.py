import json
from postagemq.encoders import encoder as e


class JsonEncoder(e.Encoder):
    """A simple JSON encoder and decoder"""

    content_type = "application/json"

    @classmethod
    def encode(cls, data):
        return json.dumps(data)

    @classmethod
    def decode(cls, string):
        return json.loads(string)
