from api.service import handle_ticker_delete
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
            ticker = data['instrument_ticker']
            await handle_ticker_delete(ticker)
        except Exception as e:
            print(f"Ошибка при обработке отмене ордеров после удаления тикера: {e}")


async def start_consumer():
    delay = 3
    while True:
        connection = None
        try:
            connection = await connect_robust(RABBITMQ_URL, timeout=10)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            exchange = await channel.declare_exchange("instrument_deletion_exchange", ExchangeType.FANOUT, durable=True)
            queue = await channel.declare_queue("instrument_deletion_exchange.ORDER", durable=True, arguments={
                "x-queue-mode": "lazy",
                "x-message-ttl": 60000,
                "x-max-length": 10000,
                "x-overflow": "drop-head"
            })
            await queue.bind(exchange)
            await queue.consume(on_message)
            await shutdown_event.wait()
        except Exception:
            print("Ошибка в консюмере удаления инструмента в ордер сервисе")
            await asyncio.sleep(delay)
            delay = min(delay*2, 30)
        finally:
            if connection and not connection.is_closed:
                await connection.close()
