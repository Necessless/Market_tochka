import aio_pika
import json
import uuid
from config import settings
import asyncio
from contextlib import asynccontextmanager


class BaseProducer:
    RABBITMQ_URL = settings.rabbitmq.url
    CONNECT_TIMEOUT = 10
    PUBLISH_TIMEOUT = 5

    def __init__(self):
        self.connection = None
        self.channel = None
        self._lock = asyncio.Lock()
        self._exchanges = {}  

    async def connect(self):
        async with self._lock:
            if not self.connection or self.connection.is_closed:
                self.connection = await asyncio.wait_for(
                    aio_pika.connect_robust(
                        self.RABBITMQ_URL,
                        client_properties={"connection_name": "base_producer"}
                    ),
                    timeout=self.CONNECT_TIMEOUT
                )
                print("Connected to RabbitMQ")

            if not self.channel or self.channel.is_closed:
                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=1)
                print("Channel created")

    async def close(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        print("Connection closed")

    @asynccontextmanager
    async def get_exchange(self, exchange_name: str, exchange_type: aio_pika.ExchangeType):
        await self.connect()
        if exchange_name not in self._exchanges:
            exchange = await self.channel.declare_exchange(
                exchange_name,
                exchange_type,
                durable=True
            )
            self._exchanges[exchange_name] = exchange
        yield self._exchanges[exchange_name]

    async def _publish_message(self, exchange_name: str, exchange_type: aio_pika.ExchangeType, message_data: dict):
        try:
            async with self.get_exchange(exchange_name, exchange_type) as exchange:
                message_body = json.dumps(message_data).encode()
                message = aio_pika.Message(
                    body=message_body
                )
                await asyncio.wait_for(
                    exchange.publish(message, routing_key=""),
                    timeout=self.PUBLISH_TIMEOUT
                )
                print(f"Message published to {exchange_name}: {message_data}")
        except Exception as e:
            print(f"Failed to publish to {exchange_name}: {str(e)}")
            raise

    async def publish_message_instrument(self, ticker: str):
        await self._publish_message(
            exchange_name="instrument_deletion_exchange",
            exchange_type=aio_pika.ExchangeType.FANOUT,
            message_data={"instrument_ticker": ticker}
        )

    async def publish_message_user(self, user_id: uuid.UUID):
        await self._publish_message(
            exchange_name="user_deletion_exchange",
            exchange_type=aio_pika.ExchangeType.FANOUT,
            message_data={"user_id": str(user_id)}
        )


instrument_producer = BaseProducer()
user_producer = BaseProducer()