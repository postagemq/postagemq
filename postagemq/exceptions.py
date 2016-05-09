class FilterError(Exception):
    """This exception is used to signal that a filter encountered some
    problem with the incoming message."""
    pass


class RejectMessage(ValueError):
    """This exception is used to signal that one of the filters
    rejected the message"""
    pass


class AckAndRestart(ValueError):
    """This exception is used to signal that the message must be acked
    and the application restarted"""
    pass


class TimeoutError(Exception):
    """An exception used to notify a timeout error while
    consuming from a given queue"""

