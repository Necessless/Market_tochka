import aio_pika
import json
from config import settings
from models import Order


class Base_Producer:
    RABBITMQ_URL = settings.rabbitmq.url

    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        if self.connection is None or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(self.RABBITMQ_URL)
        if self.channel is None or self.channel.is_closed:
            self.channel = await self.connection.channel()

    async def publish_order(self, order_data: Order):
        await self.connect()
        queue_name = "orders_queue"
        await self.channel.declare_queue(queue_name, durable=True)
        message_body = json.dumps(order_data.as_dict()).encode()
        message = aio_pika.Message(body=message_body)
        await self.channel.default_exchange.publish(message, routing_key=queue_name)


producer = Base_Producer()

