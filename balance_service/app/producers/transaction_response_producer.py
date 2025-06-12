import aio_pika
import json
from config import settings
import asyncio
from schemas.responses import Transaction_Response


class TransactionResponseProducer:
    RABBITMQ_URL = settings.rabbitmq.url
    CONNECT_TIMEOUT = 10
    QUEUE_NAME = "balance_transactions_events"
    PUBLISH_TIMEOUT = 5

    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None

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
            self.queue = await self.channel.declare_queue("balance_transactions_events", durable=True, arguments={
                "x-queue-mode": "lazy",
                "x-message-ttl": 60000,
                "x-max-length": 10000,
                "x-overflow": "drop-head"
            })

    async def close(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def publish_message(self, transaction_data: Transaction_Response):
        try:
            message_body = json.dumps(transaction_data.model_dump(mode="json")).encode()
            message = aio_pika.Message(
                body=message_body
            )
            await asyncio.wait_for(
                self.channel.default_exchange.publish(
                    message,
                    routing_key=self.QUEUE_NAME
                ),
                timeout=self.PUBLISH_TIMEOUT
            )
            print("Message published")
        except Exception as e:
            print(f"Failed to publish message: {str(e)}")
            raise


producer = TransactionResponseProducer()

