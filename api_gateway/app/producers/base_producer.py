import aio_pika
import json
import uuid
from config import settings


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
            await self.channel.set_qos(prefetch_count=5)

    async def publish_message_instrument(self, ticker: str):
        await self.connect()
        exchange_name = "instrument_deletion_exchange"
        exchange = await self.channel.declare_exchange(exchange_name, aio_pika.ExchangeType.FANOUT, durable=True)
        message_body = json.dumps({"instrument_ticker": ticker}).encode()
        message = aio_pika.Message(body=message_body)
        await exchange.publish(message, routing_key="")

    async def publish_message_user(self, user_id: uuid.UUID):
        await self.connect()
        exchange_name = "user_deletion_exchange"
        exchange = await self.channel.declare_exchange(exchange_name, aio_pika.ExchangeType.FANOUT, durable=True)
        message_body = json.dumps({"user_id": str(user_id)}).encode()
        message = aio_pika.Message(body=message_body)
        await exchange.publish(message, routing_key="")


producer = Base_Producer()