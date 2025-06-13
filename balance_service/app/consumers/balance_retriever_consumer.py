from functools import partial
from api.service import get_balance_for_user_by_ticker, deposit_on_balance
from schemas.balance_DTO import Deposit_Withdraw_Instrument_V1
import json
from uuid import UUID
from aio_pika import connect_robust, IncomingMessage, Message
from config import settings
import asyncio
from schemas.responses import BalanceGetResponse


RABBITMQ_URL = settings.rabbitmq.url
shutdown_event = asyncio.Event()


async def on_message(message: IncomingMessage, channel):
    async with message.process():
        corr_id = None
        reply_to = message.reply_to  
        available = 0

        try:
            data = json.loads(message.body)
            corr_id = data.get("correlation_id")
            user_id = UUID(data.get("user_id"))
            ticker = data.get("ticker")

            result = await get_balance_for_user_by_ticker(user_id=user_id, ticker=ticker)
            available = result._available
        except Exception as e:
            print(f"Ошибка обработки запроса баланса: {str(e)}")

        if corr_id and reply_to:
            response = BalanceGetResponse(
                available=available,
                correlation_id=corr_id
            )
            response_body = json.dumps(response.model_dump(mode='json')).encode()

            await channel.default_exchange.publish(
                Message(
                    body=response_body,
                    correlation_id=corr_id
                ),
                routing_key=reply_to
            )


async def start_consumer():
    delay = 3
    while True:
        connection = None
        try:
            connection = await connect_robust(RABBITMQ_URL, timeout=10)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            queue = await channel.declare_queue("get_balance_queue", durable=True, arguments={
                "x-queue-mode": "lazy",
                "x-message-ttl": 60000,
                "x-max-length": 10000,
                "x-overflow": "drop-head"
                })
            await queue.consume(partial(on_message, channel=channel))
            await shutdown_event.wait()
        except Exception:
            print("Ошибка при обработке транзакции вывода замороженных средств с баланса")
            await asyncio.sleep(delay)
            delay = min(delay*2, 30)
        finally:
            if connection and not connection.is_closed:
                await connection.close()
