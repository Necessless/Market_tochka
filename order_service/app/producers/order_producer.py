import aio_pika
import json
from config import settings
from models import Order
import asyncio
from contextlib import asynccontextmanager


class OrderProducer:
    RABBITMQ_URL = settings.rabbitmq.url
    CONNECT_TIMEOUT = 10
    QUEUE_NAME = "orders_queue"
    PUBLISH_TIMEOUT = 5

    def __init__(self):
        self.connection = None
        self.channel = None

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

    @asynccontextmanager
    async def get_channel(self):
        await self.connect()
        try:
            yield self.channel
        except Exception as e:
            print(f"Channel operation failed: {str(e)}")
            await self.close()
            raise

    async def close(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def publish_order(self, order_data: Order):
        try:
            async with self.get_channel() as channel:
                message_body = json.dumps(order_data.as_dict()).encode()
                message = aio_pika.Message(
                    body=message_body
                )
                
                await asyncio.wait_for(
                    channel.default_exchange.publish(
                        message,
                        routing_key=self.QUEUE_NAME
                    ),
                    timeout=self.PUBLISH_TIMEOUT
                )
                print(f"Order published: {order_data.id}")
        except Exception as e:
            print(f"Failed to publish order {order_data.id}: {str(e)}")
            raise


producer = OrderProducer()

