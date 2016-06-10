from threading import Thread
import pika
import uuid

class Producer(Thread):


    def __init__(self, message, host, port, routing_key):
        Thread.__init__(self)
        self.connection = None
        self.channel = None
        self.response = None
        self.callback_queue = None
        self.host = host
        self.message = message
        self.port = port
        self.routing_key = routing_key
        self.setupConnection()
        self.call()


    def setupConnection(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port))

        self.channel = self.connection.channel()
        self.channel.confirm_delivery()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def call(self):
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key=self.routing_key,
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue,
                                       correlation_id=self.corr_id,
                                       content_type='application/json'
                                   ),
                                   body=self.message)
        while self.response is None:
            self.connection.process_data_events()
        return self.response

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def run(self):
        self.setupConnection()




if __name__ == '__main__':
    test = Producer("message", '127.0.0.1', 5672, 'rpc_queue')
    test.call()
    print test.response
