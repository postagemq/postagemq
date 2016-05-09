from postagemq import exchange as xch

class EchoExchange(xch.Exchange):
    name = "echo-exchange"
    exchange_type = "direct"
    passive = False
    durable = True
    auto_delete = True