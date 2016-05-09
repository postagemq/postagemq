from postagemq import generic_producer as gp
import echo_shared

class EchoProducer(gp.GenericProducer):
    eks = [(echo_shared.EchoExchange, 'echo-rk')]

producer = EchoProducer()
producer.message_echo("A test message")
producer.message_quit()