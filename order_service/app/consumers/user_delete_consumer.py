from api.service import handle_user_delete
import json
from aio_pika import ExchangeType, connect_robust, IncomingMessage
from config import settings
import asyncio

RABBITMQ_URL = settings.rabbitmq.url


async def on_message(message: IncomingMessage):
    async with message.process():
        try:
            data = json.loads(message.body)
            user_id = data['user_id']
            await handle_user_delete(user_id)
        except Exception as e:
            print(f"Ошибка при обработке отмены ордеров удаленного пользователя: {e}")


async def start_consumer():
    while True:
        try:
            connection = await connect_robust(RABBITMQ_URL)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            exchange = await channel.declare_exchange("user_deletion_exchange", ExchangeType.FANOUT, durable=True)
            queue = await channel.declare_queue("user_deletion_exchange.ORDER", durable=True, auto_delete=True, arguments={
                "x-queue-mode": "lazy",
                "x-message-ttl": 60000,
                "x-max-length": 10000,
                "x-overflow": "drop-head"
            })
            await queue.bind(exchange)
            await queue.consume(on_message)
            await asyncio.Future()
        except Exception:
            print("Ошибка при обработке удаления юзера в консюмере в ордер сервисе")
            await asyncio.sleep(3)

