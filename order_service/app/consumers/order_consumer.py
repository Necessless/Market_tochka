from api.service import handle_order_creation
import json
from aio_pika import connect_robust, IncomingMessage
from config import settings
from models import Order
import asyncio

RABBITMQ_URL = settings.rabbitmq.url
shutdown_event = asyncio.Event()


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
    delay = 3 
    while True:
        connection = None
        try:
            connection = await connect_robust(RABBITMQ_URL, timeout=10)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            queue = await channel.declare_queue("orders_queue", durable=True, arguments={
                "x-queue-mode": "lazy",
                "x-message-ttl": 60000,
                "x-max-length": 10000,
                "x-overflow": "drop-head"
            })
            await queue.consume(on_message)
            await shutdown_event.wait()
        except Exception:
            print("Ошибка при обработке создания ордера в консюмере в ордер сервисе")
            await asyncio.sleep(delay)
            delay = min(delay*2, 30)
        finally:
            if connection and not connection.is_closed:
                await connection.close()

