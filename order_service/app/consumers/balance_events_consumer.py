from saga_manager import manager
import json
from aio_pika import ExchangeType, connect_robust, IncomingMessage
from config import settings
import asyncio

RABBITMQ_URL = settings.rabbitmq.url

shutdown_event = asyncio.Event()


async def on_message(message: IncomingMessage):
    async with message.process():
        try:
            data = json.loads(message.body)
            correlation_id = data.get('correlation_id')
            sub_id = data.get('sub_id')
            success = data.get('success', False)
            manager.record_result(correlation_id, sub_id, success)
        except Exception as e:
            print(f"Ошибка при обработке сообщения о транзакции: {str(e)}")


async def start_consumer():
    delay = 3
    while True:
        connection = None
        try:
            connection = await connect_robust(RABBITMQ_URL, timeout=10)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            queue = await channel.declare_queue("balance_transactions_events", durable=True, arguments={
                "x-queue-mode": "lazy",
                "x-message-ttl": 60000,
                "x-max-length": 10000,
                "x-overflow": "drop-head"
            })
            await queue.consume(on_message)
            await shutdown_event.wait()
        except Exception:
            print("Ошибка в консюмере обработки статуса транзакций")
            await asyncio.sleep(delay)
            delay = min(delay*2, 30)
        finally:
            if connection and not connection.is_closed:
                await connection.close()
