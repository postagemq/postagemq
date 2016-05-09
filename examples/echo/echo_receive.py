from __future__ import print_function
from postagemq import microthreads
from postagemq import message_processor as mp
from postagemq import handlers as hdl
import echo_shared


class EchoReceiveProcessor(mp.MessageProcessor):
    @hdl.MessageHandler('command', 'echo')
    def msg_echo(self, content):
        print(content['parameters'])

eqk = [(echo_shared.EchoExchange, [('echo-queue', 'echo-rk'), ])]

scheduler = microthreads.MicroScheduler()
scheduler.add_microthread(EchoReceiveProcessor({}, eqk, None, None))
for i in scheduler.main():
    pass