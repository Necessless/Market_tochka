from typing import Dict
import aio_pika
import json
from config import settings
from api.schemas import GetBalanceDTO
import asyncio
from contextlib import asynccontextmanager


class GetBalanceProducer:
    RABBITMQ_URL = settings.rabbitmq.url
    CONNECT_TIMEOUT = 10
    QUEUE_NAME = "get_balance_queue"
    PUBLISH_TIMEOUT = 5

    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None

    @asynccontextmanager
    async def get_channel(self):
        await self.connect()
        try:
            yield self.channel
        except Exception as e:
            print(f"Channel operation failed: {str(e)}")
            await self.close()
            raise

    async def connect(self):
        if self.connection is None or self.connection.is_closed:
            try:
                self.connection = await asyncio.wait_for(
                    aio_pika.connect_robust(
                        self.RABBITMQ_URL
                    ),
                    timeout=self.CONNECT_TIMEOUT
                )
                print("Connected to RabbitMQ")
            except Exception as e:
                print(f"Connection failed: {str(e)}")
                raise

        if self.channel is None or self.channel.is_closed:
            self.channel = await self.connection.channel()
            await self.channel.declare_queue(
                self.QUEUE_NAME,
                durable=True,
                arguments={
                    "x-queue-mode": "lazy",
                    "x-message-ttl": 60000,
                    "x-max-length": 10000,
                    "x-overflow": "drop-head"
                }
            )

    async def close(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def call(self, balance_data: GetBalanceDTO) -> dict:
        async with self.get_channel() as channel:
            callback_queue = await channel.declare_queue(exclusive=True)

            future = asyncio.get_event_loop().create_future()

            async def on_response(message: aio_pika.IncomingMessage):
                if message.correlation_id == balance_data.correlation_id:
                    future.set_result(json.loads(message.body.decode()))

            consumer_tag = await callback_queue.consume(on_response)
            request_body = json.dumps(balance_data.model_dump(mode="json")).encode()
            message = aio_pika.Message(
                body=request_body,
                correlation_id=balance_data.correlation_id,
                reply_to=callback_queue.name
            )

            await channel.default_exchange.publish(
                message,
                routing_key=self.QUEUE_NAME
            )

            try:
                result = await asyncio.wait_for(future, timeout=self.CONNECT_TIMEOUT)
                return result
            except asyncio.TimeoutError:
                raise TimeoutError("Ответ от сервиса баланса не получен")
            finally:
                await callback_queue.cancel(consumer_tag)


producer = GetBalanceProducer()

