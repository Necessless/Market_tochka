import aio_pika
import json
import uuid
from config import settings
RABBITMQ_URL = settings.rabbitmq.url


async def publish_message(user_id: uuid.UUID):
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    
    async with connection:
        channel = await connection.channel()
        queue_name = "user_deletion_exchange"
        exchange = await channel.declare_exchange(queue_name, aio_pika.ExchangeType.FANOUT, durable=True)

        message_body = json.dumps({"user_id": str(user_id)}).encode()
        message = aio_pika.Message(body=message_body)

        await exchange.publish(message, routing_key="")
