from api.service import handle_user_delete
import json
from aio_pika import ExchangeType, connect_robust, IncomingMessage
from config import settings

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
    connection = await connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange("user_deletion_exchange", ExchangeType.FANOUT, durable=True)
    queue = await channel.declare_queue("user_deletion_exchange.ORDER", durable=True)
    await queue.bind(exchange)
    await queue.consume(on_message)

