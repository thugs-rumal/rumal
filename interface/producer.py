#!/usr/bin/env python
#
# models.py
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA  02111-1307  USA
#
# Author:   Pietro Delsante <pietro.delsante@gmail.com>
#           The Honeynet Project
#

from threading import Thread
import pika
import uuid
import time
from interface.utils import TimeOutException

class Producer(Thread):

    TIME_OUT = 5 * 60  # Set timeout for receiving messages to 10mn

    def __init__(self, message, host, port, routing_key, frontend_id):
        Thread.__init__(self)
        self.frontend_id = frontend_id
        self.connection = None
        self.channel = None
        self.response = None
        self.callback_queue = None
        self.host = host
        self.message = message
        self.port = port
        self.routing_key = routing_key
        self.thread_exception = None


    def setupConnection(self):
        try:
            credentials = pika.PlainCredentials('admin', 'admin')
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,
                                                                                port=self.port,
                                                                                #credentials=credentials
                                                                                )
                                                      )

            self.channel = self.connection.channel()
            self.channel.confirm_delivery()

            result = self.channel.queue_declare(exclusive=True)
            self.callback_queue = result.method.queue

            self.channel.basic_consume(self.on_response, no_ack=True,
                                       queue=self.callback_queue)
        except pika.exceptions.ConnectionClosed :
            raise pika.exceptions.ConnectionClosed

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
        start_timer = time.time()
        while self.response is None:
            current_time = time.time()
            if (current_time - start_timer >= self.TIME_OUT):
                raise TimeOutException
            self.connection.process_data_events()

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def run(self):
        try:
            self.setupConnection()
            self.call()
        except pika.exceptions.ConnectionClosed:
            self.thread_exception = pika.exceptions.ConnectionClosed
        except TimeOutException:
            self.thread_exception = TimeOutException


if __name__ == '__main__':
    test = Producer("message", '127.0.0.1', 5672, 'rpc_queue')
    test.start()
    time.sleep(4)
    print test.thread_exception

