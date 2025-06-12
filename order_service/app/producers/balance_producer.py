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
            self.exchange = await self.channel.declare_exchange(self.EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True)

    async def close(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def publish_message(self, transaction_data: BaseBalanceDTO):
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
            print(f"Publishing: correlation={transaction_data.correlation_id}, sub_id={transaction_data.sub_id}")
        except Exception as e:
            print(f"Failed to publish message: {str(e)}")
            raise

producer = BalanceProducer()

