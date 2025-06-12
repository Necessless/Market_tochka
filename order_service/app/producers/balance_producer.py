from typing import Dict
import aio_pika
import json
from config import settings
from api.schemas import BaseBalanceDTO
import asyncio
from contextlib import asynccontextmanager
import uuid

class BalanceProducer:
    RABBITMQ_URL = settings.rabbitmq.url
    CONNECT_TIMEOUT = 10
    EXCHANGE_NAME = "Balance_change_exchange"
    PUBLISH_TIMEOUT = 5

    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.messages_cache = set()
        self._futures: Dict[str, asyncio.Future] = {}

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
            self.exchange = await self.channel.declare_exchange(self.EXCHANGE_NAME, aio_pika.ExchangeType.FANOUT, durable=True)

    async def close(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def publish_message(self, transaction_data: BaseBalanceDTO):
        
        correlation_id = uuid.uuid4()
        transaction_data.correlation_id = correlation_id
        future = asyncio.get_event_loop().create_future()
        self._futures[correlation_id] = future
        try:
            message_body = json.dumps(transaction_data.model_dump(mode="json")).encode()
            message = aio_pika.Message(
                body=message_body
            )
            await asyncio.wait_for(
                self.exchange.publish(
                    message, 
                    routing_key=transaction_data.direction.value
                ),
                timeout=self.PUBLISH_TIMEOUT
            )
            print(f"Message published")
        try:
            result = await asyncio.wait_for(future, timeout=10)
            del self._futures[correlation_id]
            return result
        except asyncio.TimeoutError:
            print(f"No confirmation received for correlation_id={correlation_id}")
            del self._futures[correlation_id]
            return False
        except Exception as e:
            print(f"Failed to publish message: {str(e)}")
            raise

producer = BalanceProducer()

