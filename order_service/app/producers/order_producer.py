import aio_pika
import json
from config import settings
from models import Order
RABBITMQ_URL = settings.rabbitmq.url


async def publish_order(order_data: Order):
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    
    async with connection:
        channel = await connection.channel()
        queue_name = "orders_queue"
        await channel.declare_queue(queue_name, durable=True)

        message_body = json.dumps(order_data.as_dict()).encode()
        message = aio_pika.Message(body=message_body)

        await channel.default_exchange.publish(message, routing_key=queue_name)
