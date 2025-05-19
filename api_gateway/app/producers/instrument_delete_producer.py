import aio_pika
import json
from config import settings

RABBITMQ_URL = settings.rabbitmq.url


async def publish_message(ticker: str):
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    
    async with connection:
        channel = await connection.channel()
        queue_name = "instrument_deletion_exchange"
        exchange = await channel.declare_exchange(queue_name, aio_pika.ExchangeType.FANOUT, durable=True)

        message_body = json.dumps({"instrument_ticker": ticker}).encode()
        message = aio_pika.Message(body=message_body)

        await exchange.publish(message, routing_key=queue_name)
