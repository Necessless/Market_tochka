from api.service import handle_ticker_delete
import json
from aio_pika import ExchangeType, connect_robust, IncomingMessage
from config import settings

RABBITMQ_URL = settings.rabbitmq.url


async def on_message(message: IncomingMessage):
    async with message.process():
        try:
            data = json.loads(message.body)
            ticker = data['instrument_ticker']
            await handle_ticker_delete(ticker)
        except Exception as e:
            print(f"Ошибка при обработке удаления тикера: {e}")


async def start_consumer():
    connection = await connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange("instrument_deletion_exchange", ExchangeType.FANOUT, durable=True)
    queue = await channel.declare_queue("instrument_deletion_exchange.BALANCE", durable=True)
    await queue.bind(exchange)
    await queue.consume(on_message)

