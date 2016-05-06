import os
import socket
import getpass


class Fingerprint(object):
    """The fingerprint of a component.
    This class encompasses all the values the library uses to identify the
    component in the running system.
    """

    def __init__(self, name, vhost, type=None, pid=os.getpid(),
                 host=socket.gethostname(), user=getpass.getuser()):
        self.name = str(name)
        self.type = str(type)
        self.pid = str(pid)
        self.host = str(host)
        self.user = str(user)
        self.vhost = str(vhost)

    def as_dict(self):
        return {'name': self.name, 'type': self.type, 'pid': self.pid,
                'host': self.host, 'user': self.user, 'vhost': self.vhost}

    def as_tuple(self):
        return (self.name, self.type, self.pid, self.host,
                self.user, self.vhost)