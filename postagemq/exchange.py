import six


class ExchangeType(type):
    """A metaclass to type exchanges.
    This allows us to declare exchanges just by setting class attributes.
    Exchanges can then be used without instancing the class.
    """

    def __init__(self, name, bases, dic):
        super(ExchangeType, self).__init__(name, bases, dic)
        self.parameters = {
            "exchange": self.name,
            "exchange_type": self.exchange_type,
            "passive": self.passive,
            "durable": self.durable,
            "auto_delete": self.auto_delete
        }


class Exchange(six.with_metaclass(ExchangeType, object)):
    """A generic exchange.
    This objects helps the creation of an exchange and its use among
    different programs, encapsulating the parameters. Since exchanges can be
    declared again and again an application can always instance
    this object.

    This object has to be inherited and customized.
    """

    name = "noname"
    exchange_type = "direct"
    passive = False
    durable = True
    auto_delete = False
