from api.service import handle_order_creation
import json
from aio_pika import connect_robust, IncomingMessage
from config import settings
from models import Order
import asyncio

RABBITMQ_URL = settings.rabbitmq.url


async def on_message(message: IncomingMessage):
    async with message.process():
        try:
            data = json.loads(message.body)
            print(data)
            order = Order(**data)
            await handle_order_creation(order)
        except Exception as e:
            print(f"Ошибка при обработке ордера: {e}")


async def start_consumer():
    while True:
        try:
            connection = await connect_robust(RABBITMQ_URL)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            queue = await channel.declare_queue("orders_queue", durable=True)
            await queue.consume(on_message)
            await asyncio.Future()
        except Exception:
            print("Ошибка при обработке создания ордера в консюмере в ордер сервисе")
            await asyncio.sleep(3)

